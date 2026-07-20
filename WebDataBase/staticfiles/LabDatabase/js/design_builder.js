const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
const geneInput = document.getElementById('geneSearch');
const geneResults = document.getElementById('geneResults');
const geneIdInput = document.getElementById('gene_id');
const designForm = document.getElementById('designForm');
const resetButton = document.getElementById('resetDesign');
const summaryEmpty = document.getElementById('summaryEmpty');
const summaryContent = document.getElementById('summaryContent');
const selectedModules = document.getElementById('selectedModules');
const predictedExpression = document.getElementById('predictedExpression');
const repositoryName = document.getElementById('repositoryName');
const taskStatusBox = document.getElementById('taskStatusBox');
const downloadLink = document.getElementById('downloadLink');
const repoLink = document.getElementById('repoLink');
const formulaPreview = document.getElementById('formulaPreview');
const repositoryVisual = document.getElementById('repositoryVisual');
const repositoryVisualName = document.getElementById('repositoryVisualName');
const repositoryPartsList = document.getElementById('repositoryPartsList');
const repositoryBackboneName = document.getElementById('repositoryBackboneName');
const repositoryBackboneAlias = document.getElementById('repositoryBackboneAlias');
const repositoryBackboneSpecies = document.getElementById('repositoryBackboneSpecies');
const repositoryBackboneStrength = document.getElementById('repositoryBackboneStrength');
const promoterPresets = JSON.parse(document.getElementById('promoter-strength-presets').textContent);
const rbsPresets = JSON.parse(document.getElementById('rbs-strength-presets').textContent);
const terminatorPresets = JSON.parse(document.getElementById('terminator-strength-presets').textContent);

const promoterInput = document.getElementById('promoter_strength');
const rbsInput = document.getElementById('rbs_strength');
const terminatorInput = document.getElementById('terminator_strength');
const expressionInput = document.getElementById('expression_strength');
const geneSearchButton = document.getElementById('geneSearchButton');
const screenTabs = document.querySelectorAll('[data-screen-target]');
const screens = document.querySelectorAll('.screen');

let geneSearchTimer = null;

function parseNumber(value) {
    if (value === '' || value === null || value === undefined) {
        return null;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function renderGeneResults(items) {
    geneResults.innerHTML = '';
    if (!items.length) {
        geneResults.innerHTML = '<div class="search-item">没有找到匹配基因</div>';
        return;
    }

    items.forEach((item) => {
        const div = document.createElement('div');
        div.className = 'search-item';
        div.innerHTML = `
            <strong>${item.name}</strong>
            <div>${item.alias || '无别名'}</div>
            <div class="muted">${item.source || '未知来源'} · ${item.length} bp</div>
        `;
        div.addEventListener('click', () => {
            geneInput.value = `${item.name}${item.alias ? ` (${item.alias})` : ''}`;
            geneIdInput.value = item.id;
            geneResults.innerHTML = '';
        });
        geneResults.appendChild(div);
    });
}

async function searchGenes(query) {
    const response = await fetch(`/LabDatabase/design-builder/gene-search?q=${encodeURIComponent(query)}`);
    const result = await response.json();
    renderGeneResults(result.data || []);
}

function activateScreen(screenId) {
    screens.forEach((screen) => {
        screen.classList.toggle('active', screen.id === screenId);
    });
    screenTabs.forEach((tab) => {
        tab.classList.toggle('active', tab.dataset.screenTarget === screenId);
    });
}

geneInput.addEventListener('input', () => {
    geneIdInput.value = '';
    const query = geneInput.value.trim();
    clearTimeout(geneSearchTimer);
    geneSearchTimer = setTimeout(() => {
        searchGenes(query);
    }, 250);
});

if (geneSearchButton) {
    geneSearchButton.addEventListener('click', () => {
        searchGenes(geneInput.value.trim());
    });
}

screenTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
        activateScreen(tab.dataset.screenTarget);
    });
});

function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(value)) {
        return '-';
    }
    return Number(value).toFixed(4).replace(/\.?0+$/, '');
}

function findDiscreteSolution(targetExpression, provided) {
    let bestSolution = null;
    let bestError = null;
    let bestDistance = null;

    const promoterCandidates = provided.promoter !== null ? [provided.promoter] : promoterPresets;
    const rbsCandidates = provided.rbs !== null ? [provided.rbs] : rbsPresets;
    const terminatorCandidates = provided.terminator !== null ? [provided.terminator] : terminatorPresets;

    promoterCandidates.forEach((promoter) => {
        rbsCandidates.forEach((rbs) => {
            terminatorCandidates.forEach((terminator) => {
                const expression = promoter * rbs * terminator;
                const error = Math.abs(expression - targetExpression);
                const distance =
                    Math.abs(promoter - (provided.promoter ?? promoter)) +
                    Math.abs(rbs - (provided.rbs ?? rbs)) +
                    Math.abs(terminator - (provided.terminator ?? terminator));

                if (
                    bestSolution === null ||
                    error < bestError ||
                    (error === bestError && distance < bestDistance)
                ) {
                    bestSolution = { promoter, rbs, terminator, expression };
                    bestError = error;
                    bestDistance = distance;
                }
            });
        });
    });

    return bestSolution;
}

function updateFormulaPreview() {
    const promoter = parseNumber(promoterInput.value);
    const rbs = parseNumber(rbsInput.value);
    const terminator = parseNumber(terminatorInput.value);
    const expression = parseNumber(expressionInput.value);
    const values = { promoter, rbs, terminator };
    const missingKeys = Object.keys(values).filter((key) => values[key] === null);

    if (expression !== null) {
        if (missingKeys.length === 0) {
            const computed = promoter * rbs * terminator;
            formulaPreview.textContent = `已填写三项元件强度，按公式计算目标表达强度 = ${formatNumber(computed)}。`;
            return;
        }

        const solution = findDiscreteSolution(expression, values);
        if (!solution) {
            formulaPreview.textContent = '当前输入无法在离散强度空间中找到可用组合。';
            return;
        }

        formulaPreview.textContent = `按目标表达强度 ${formatNumber(expression)} 在离散空间搜索，最优组合为 Promoter=${formatNumber(solution.promoter)}，RBS=${formatNumber(solution.rbs)}，Terminator=${formatNumber(solution.terminator)}，得到表达强度 ${formatNumber(solution.expression)}。`;
        return;
    }

    if (missingKeys.length === 0) {
        const computed = promoter * rbs * terminator;
        formulaPreview.textContent = `当前目标表达强度将由元件强度直接计算：${formatNumber(promoter)} × ${formatNumber(rbs)} × ${formatNumber(terminator)} = ${formatNumber(computed)}。`;
        return;
    }

    formulaPreview.textContent = '请输入目标表达强度，或填写启动子、RBS、终止子三项后自动计算。';
}

[promoterInput, rbsInput, terminatorInput, expressionInput].forEach((input) => {
    input.addEventListener('input', updateFormulaPreview);
});

function renderSelectionCard(title, name, strength) {
    const div = document.createElement('div');
    div.className = 'summary-card';
    div.innerHTML = `
        <div class="muted">${title}</div>
        <strong>${name}</strong>
        <div>强度: ${strength === null ? 'N/A' : formatNumber(strength)}</div>
    `;
    return div;
}

function renderRepositoryPartChip(title, item) {
    const div = document.createElement('div');
    div.className = 'part-chip';
    div.innerHTML = `
        <div>
            <small>${title}</small>
            <strong>${item.name || '-'}</strong>
        </div>
        <div class="muted-line">Strength: ${item.strength === null || item.strength === undefined ? 'N/A' : formatNumber(item.strength)}</div>
    `;
    return div;
}

function renderRepositoryVisualization(repository, parts, backbone) {
    repositoryVisual.style.display = 'block';
    repositoryVisualName.textContent = repository || '-';
    repositoryPartsList.innerHTML = '';

    const labels = ['Promoter', 'RBS', 'CDS', 'Terminator'];
    parts.forEach((item, index) => {
        repositoryPartsList.appendChild(renderRepositoryPartChip(labels[index] || 'Part', item));
    });

    repositoryBackboneName.textContent = backbone?.name || '-';
    repositoryBackboneAlias.textContent = `Alias: ${backbone?.alias || '-'}`;
    repositoryBackboneSpecies.textContent = `Species: ${backbone?.species || '-'}`;
    repositoryBackboneStrength.textContent = `Reference strength: ${
        backbone?.strength === null || backbone?.strength === undefined ? '-' : formatNumber(backbone.strength)
    }`;
}

function resetRepositoryVisualization() {
    repositoryVisual.style.display = 'none';
    repositoryVisualName.textContent = '-';
    repositoryPartsList.innerHTML = '';
    repositoryBackboneName.textContent = '-';
    repositoryBackboneAlias.textContent = 'Alias: -';
    repositoryBackboneSpecies.textContent = 'Species: -';
    repositoryBackboneStrength.textContent = 'Reference strength: -';
}

function updateTaskStatus(message) {
    taskStatusBox.textContent = message;
}

async function pollTask(taskId, repository) {
    const timer = setInterval(async () => {
        const response = await fetch(`/LabDatabase/task_status/${taskId}`);
        const result = await response.json();

        if (result.status === 'processing') {
            updateTaskStatus(`后台组装中，当前进度 ${result.progress || 0}%`);
            return;
        }

        clearInterval(timer);
        if (result.status === 'completed') {
            updateTaskStatus('组装完成，结果已生成');
            if (result.result && result.result.download_url) {
                downloadLink.href = result.result.download_url;
                downloadLink.style.display = 'inline-block';
            }
            repoLink.href = `/LabDatabase/ShowRepository/${repository}`;
            repoLink.style.display = 'inline-block';
        } else {
            updateTaskStatus(`组装失败: ${result.error || '未知错误'}`);
        }
    }, 2000);
}

designForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!geneIdInput.value) {
        alert('请先从搜索结果中选择一个表达基因');
        return;
    }

    const payload = {
        chassis: document.querySelector('input[name="chassis"]:checked').value || 'ecoli',
        gene_id: Number(geneIdInput.value),
        promoter_strength: promoterInput.value.trim(),
        rbs_strength: rbsInput.value.trim(),
        terminator_strength: terminatorInput.value.trim(),
        expression_strength: expressionInput.value.trim(),
    };

    const response = await fetch('/LabDatabase/design-builder/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
        alert(result.message || '设计提交失败');
        return;
    }

    summaryEmpty.style.display = 'none';
    summaryContent.style.display = 'block';
    selectedModules.innerHTML = '';

    result.selected_parts.forEach((item, index) => {
        const labels = ['Promoter', 'RBS', 'CDS', 'Terminator'];
        selectedModules.appendChild(renderSelectionCard(labels[index] || 'Part', item.name, item.strength));
    });
    selectedModules.appendChild(renderSelectionCard('Backbone / Reference', result.selected_backbone.name, result.selected_backbone.strength));

    predictedExpression.textContent = formatNumber(result.strengths.target_expression);
    repositoryName.textContent = result.repository_name;
    renderRepositoryVisualization(result.repository_name, result.selected_parts, result.selected_backbone);
    updateTaskStatus(result.message);
    downloadLink.style.display = 'none';
    repoLink.style.display = 'none';
    pollTask(result.task_id, result.repository_name);
});

resetButton.addEventListener('click', () => {
    designForm.reset();
    geneResults.innerHTML = '';
    geneIdInput.value = '';
    summaryEmpty.style.display = 'block';
    summaryContent.style.display = 'none';
    resetRepositoryVisualization();
    updateFormulaPreview();
});

updateFormulaPreview();
