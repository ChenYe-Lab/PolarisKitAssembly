let chart;
const TYPE_COLORS = {
    part: '#3498db',
    backbone: '#f39c12',
    plasmid: '#2ecc71',
    default: '#95a5a6'
};
            const plasmid_map_div = document.getElementById("plasmid-map-div");
            // '<div class="plasmid-label" style="transform: rotate(0deg) translate(220px) rotate(0deg);">{{backbone.marker}}</div>'
            // '<div class="plasmid-label" style="transform: rotate(90deg) translate(220px) rotate(-90deg);">{{backbone.ori}}</div>'
            ori_list =  document.getElementById("plasmid_marker_info").innerText.split(", ")
            marker_list = document.getElementById("plasmid_ori_info").innerText.split(", ")
            ori_length = ori_list.length
            marker_length = marker_list.length
            total_num = ori_length + marker_length
            each_deg = Math.floor(360 / total_num)
            deg = 0
            console.log(ori_list);
            console.log(marker_list);
            console.log(each_deg);
            ori_list.forEach(item =>{
                const tab = document.createElement("div");
                tab.classList.add("plasmid-label");
                tab.style.transform = `rotate(${deg}deg) translate(220px) rotate(-${deg}deg)`;
                tab.innerText = item;
                deg = deg + each_deg;
                plasmid_map_div.appendChild(tab);
            })
            marker_list.forEach(item =>{
                const tab = document.createElement("div");
                tab.classList.add("plasmid-label");
                tab.style.transform = `rotate(${deg}deg) translate(220px) rotate(-${deg}deg)`;
                tab.innerText = item;
                deg = deg + each_deg;
                plasmid_map_div.appendChild(tab);
            })
            // Add hover effect for labels
            document.querySelectorAll('.plasmid-label').forEach(label => {
                label.addEventListener('mouseover', function() {
                    this.style.backgroundColor = 'rgba(255,255,255,0.9)';
                    this.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
                    this.style.zIndex = '10';
                });
            
                label.addEventListener('mouseout', function() {
                    this.style.backgroundColor = 'rgba(255,255,255,0.7)';
                    this.style.boxShadow = 'none';
                    this.style.zIndex = '1';
                });
            });

            // parseTreeData();

            initChart();

            document.getElementById('collapseAll').addEventListener('click',collapseAllNodes);

        document.getElementById('downMapButton').addEventListener('click',function(){
            let pathname_list = window.location.pathname.split('/');
            let plasmidid = pathname_list[pathname_list.length -1];
            window.location.href = `/LabDatabase/downloadPlasmidMap/${plasmidid}`;
        })

        const partGeneratorButton = document.getElementById('part_generator');
        if (partGeneratorButton) {
            partGeneratorButton.addEventListener('click', generatePartFromPlasmid);
        }

        // Download button click feedback
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', function() {
                if (this.id === 'part_generator') {
                    return;
                }
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Downloading...';
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                    alert('Download completed');
                }, 1500);
            });
        });

        function getCleanPlasmidSequence() {
            const sequenceContainer = document.getElementById('SequenceContainer');
            if (!sequenceContainer) {
                return '';
            }
            return sequenceContainer.textContent.replace(/[^A-Za-z]/g, '').toUpperCase();
        }

        function extractCircularSequence(sequence, start, end) {
            if (start <= end) {
                return sequence.slice(start - 1, end);
            }
            return sequence.slice(start - 1) + sequence.slice(0, end);
        }

        function reverseSequence(sequence) {
            const complementMap = {
                A: 'T',
                T: 'A',
                C: 'G',
                G: 'C',
                U: 'A',
                R: 'Y',
                Y: 'R',
                S: 'S',
                W: 'W',
                K: 'M',
                M: 'K',
                B: 'V',
                V: 'B',
                D: 'H',
                H: 'D',
                N: 'N'
            };

            return sequence
                .toUpperCase()
                .split('')
                .reverse()
                .map(base => complementMap[base] || base)
                .join('');
        }

        function buildPartSequence(sequence, start, end, direction) {
            const extracted = extractCircularSequence(sequence, start, end);
            if (!extracted) {
                return '';
            }
            if (direction === 'reverse') {
                return reverseSequence(extracted);
            }
            return extracted;
        }

        async function generatePartFromPlasmid() {
            const startValue = Number(document.getElementById('start_position').value);
            const endValue = Number(document.getElementById('end_position').value);
            const partName = document.getElementById('part_name').value.trim();
            const partDirection = document.getElementById('part_direction').value;
            const partType = document.getElementById('part_type_selection').value;
            const isProkaryote = document.getElementById('part_source_prokaryote').checked;
            const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
            const csrfToken = csrfInput ? csrfInput.value : '';
            const plasmidName = document.getElementById('plasmid_name').innerText.trim();
            const sequence = getCleanPlasmidSequence();
            const sourceOrganism = isProkaryote ? 'E.coli' : 'saccharomyces';
            
            if (!partName) {
                alert('请输入元件名称');
                return;
            }
            if (!Number.isInteger(startValue) || !Number.isInteger(endValue) || startValue < 1 || endValue < 1) {
                alert('请输入合法的起始和结束位置');
                return;
            }
            if (!sequence) {
                alert('未读取到质粒序列');
                return;
            }
            if (startValue > sequence.length || endValue > sequence.length) {
                alert(`位置超出质粒长度范围，当前长度为 ${sequence.length} bp`);
                return;
            }

            const targetSequence = buildPartSequence(sequence, startValue, endValue, partDirection);
            if (!targetSequence) {
                alert('截取序列失败');
                return;
            }

            console.log(targetSequence);
            const requestBody = {
                name: partName,
                alias: '',
                Level0Sequence: targetSequence,
                ConfirmedSequence: '',
                InsertSequence: '',
                source: sourceOrganism,
                reference: `Positions ${startValue}-${endValue} (${partDirection === 'forward' ? 'forward' : 'reverse'}) from plasmid ${plasmidName}`,
                note: `Generated from plasmid ${plasmidName} with ${partDirection === 'forward' ? 'forward' : 'reverse'} direction; source=${sourceOrganism}`,
                type: partType,
            };

            partGeneratorButton.disabled = true;
            const originalText = partGeneratorButton.innerHTML;
            partGeneratorButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Saving...';

            try {
                const response = await fetch('/WebDatabase/AddPartData', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify(requestBody),
                    credentials: 'include',
                });

                // const res = await response.json();
                // let result;
                // try {
                //     result = JSON.parse(rawText);
                // } catch (error) {
                //     result = rawText;
                // }
                
                // if (!response.ok) {
                //     const message = typeof result === 'string' ? result : (result.message || '保存元件失败');
                //     alert(message);
                //     return;
                // }

                // alert(`元件 ${partName} 已保存，长度 ${targetSequence.length} bp`);
                const result = await response.json()
                if(result.success){
                    alert(`元件 ${partName} 已保存，长度 ${targetSequence.length} bp`);
                }
                else{
                    alert(result.message);
                }
            } catch (error) {
                alert(`保存元件失败: ${error.message}`);
            } finally {
                partGeneratorButton.disabled = false;
                partGeneratorButton.innerHTML = originalText;
            }
        }

        
        function initChart() {
            const chartDom = document.getElementById('plasmid_tree');
            chart = echarts.init(chartDom);

            updateChart();

            setupEventListeners();

            window.addEventListener('resize',function() {
                chart.resize();
            });
        }

        function getChartOption(treeData){
            const baseOption = {
                title:{
                    text: "Plasmid Relationship Tree",
                    left: 'center',
                    textStyle :{
                        color:'#2c3e50',
                        fontSize: 20,
                        fontWeight: 'bold'
                    }
                },
                tooltip: {
                    trigger: 'item',
                    triggerOn: 'mousemove',
                    formatter: function(params) {
                        const name = params.name;
                        const nodeType = params.data.type || 'unknown';
                        return `
                        <div style="padding: 5px;">
                            <strong>${name}</strong><br/>
                            type: ${nodeType}
                        </div>`;
                    }
                },
                series: [{type: 'tree',
                        data: [treeData],
                        top: '10%',
                        left: '10%',
                        bottom: '10%',
                        right: '30%',
                        symbolSize: 10,
                        label: {
                            position: 'left',
                            verticalAlign: 'middle',
                            align: 'right',
                            fontSize: 14,
                            fontWeight: 'bold',
                            color: '#2c3e50'
                        },
                        leaves: {
                            label: {
                                position: 'right',
                                verticalAlign: 'middle',
                                align: 'left'
                            }
                        },
                        emphasis: {
                            focus: 'descendant',
                            itemStyle: {
                                color: '#2ecc71'
                            }
                        },
                        expandAndCollapse: true,
                        initialTreeDepth: 1,
                        lineStyle: {
                            color: '#95a5a6',
                            width: 2,
                            curveness: 0.2
                        },
                        itemStyle: {
                            color: function(params) {
                                // Node color by type
                                const nodeType = params.data.type;
                                return TYPE_COLORS[nodeType] || TYPE_COLORS.default;
                            },
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        tooltip: {
                            formatter: function(params) {
                                const name = params.name;
                                const nodeType = params.data.type || 'unknown';
                                return `
                                <div style="padding: 10px; min-width: 150px;">
                                    <div style="font-weight: bold; margin-bottom: 5px;">${name}</div>
                                    <div>type: <span style="color: #3498db;">${nodeType}</span></div>
                                </div>`;
                            }
                        }
                    }
                ]
            };
            return baseOption;
        }

        async function parseTreeData(){
            try{
                const plasmidName = document.getElementById("plasmid_name").innerText;

                const response = await fetch(`/LabDatabase/GetParent?PlasmidName=${plasmidName}`);
                const data = await response.json();
                console.log(data);
                    if(data.success) {
                        // console.log(data);
                        let json_value = `{"name":"${plasmidName}","type":"plasmid","children":[`;
                        // let json_obj = JSON.parse(json_value);
                        let sub_part_value = "";
                        data.parentPart.forEach(part =>{
                            sub_part_value = sub_part_value + `{"name":"${part.name}","type":"part"},`;
                            // console.log(sub_part_value);
                        })
                        data.parentBackbone.forEach(backbone => {
                            sub_part_value = sub_part_value + `{"name":"${backbone.name}","type":"backbone"},`;
                        })
                        // let sub_backbone_obj = JSON.parse(sub_backbone_value);

                        data.parentPlasmid.forEach(plasmid => {
                            sub_part_value = sub_part_value + `{"name":"${plasmid.name}","type":"plasmid"},`
                        })
                        // let sub_plasmid_obj = JSON.parse(sub_plasmid_value);
                        data.parentInfo.Part.forEach(part => {
                            sub_part_value = sub_part_value + `{"name":"${part}","type":"part"},`
                        })

                        data.parentInfo.Backbone.forEach(backbone => {
                            sub_part_value = sub_part_value + `{"name":"${backbone}","type":"backbone"},`
                        })

                        data.parentInfo.Plasmid.forEach(plasmid => {
                            sub_part_value = sub_part_value + `{"name":"${plasmid}","type":"plasmid"},`
                        })


                        sub_part_value = sub_part_value.substring(0,sub_part_value.length-1);
                        json_value = json_value + sub_part_value + "]}";

                        console.log(json_value);
                        // let sub_list = [sub_part_obj, sub_backbone_obj, sub_plasmid_obj];
                        // json_obj.children = sub_list;

                        // let newJsonstr = JSON.stringify(json_obj);
                        // console.log(json_value);
                        console.log(JSON.parse(json_value));
                        return JSON.parse(json_value);
                        // return JSON.parse(json_value);
                    }
                    else{
                        alert(data.message);
                        return null;
                    }
                }
            catch{
                alert('无法获取Parent信息');
                return null;
            }
        }

        async function updateChart(){
            console.log("updateChart");
            let treeData = await parseTreeData();
            // console.log(treeData);
            if(! treeData) return;

            addDepthInfo(treeData);
            applyTypeStyle(treeData);
            const option = getChartOption(treeData);
            console.log(option);
            chart.setOption(option);
        }

        function addDepthInfo(node, depth = 0){
            node.depth = depth;
            console.log(node);
            if(node.children && node.children.length > 0){
                node.children.forEach(child => {
                    addDepthInfo(child, depth + 1);
                });
            }
        }

        function applyTypeStyle(node){
            const nodeType = node.type;
            node.itemStyle = {
                ...(node.itemStyle || {}),
                color: TYPE_COLORS[nodeType] || TYPE_COLORS.default,
                borderColor: '#fff',
                borderWidth: 2
            };
            if(node.children && node.children.length > 0){
                node.children.forEach(child => {
                    applyTypeStyle(child);
                });
            }
        }

        // Expand all nodes
        function expandAllNodes() {
            const option = chart.getOption();
            if (option.series && option.series[0]) {
                option.series[0].initialTreeDepth = 100; // Expand all levels
                chart.setOption(option);
            }
        }

        // Collapse all nodes
        function collapseAllNodes() {
            const option = chart.getOption();
            if (option.series && option.series[0]) {
                option.series[0].initialTreeDepth = 0;
                chart.setOption(option);
            }
        }


        // Export image
        function exportToImage() {
            const url = chart.getDataURL({
                type: 'png',
                pixelRatio: 2,
                backgroundColor: '#fff'
            });
            
            const link = document.createElement('a');
            link.download = `plasmid_relationship_${new Date().getTime()}.png`;
            link.href = url;
            link.click();
        }

        async function addNode(plasmidName){
            try{
                const response = await fetch(`/LabDatabase/GetParent?PlasmidName=${plasmidName}`);
                const data = await response.json();
                    if(data.success) {
                        // console.log(data);
                        let json_value = `{"name":"{{plasmid.name}}","children":[`;
                        // let json_obj = JSON.parse(json_value);
                        let sub_part_value = "";
                        data.parentPart.forEach(part =>{
                            sub_part_value = sub_part_value + `{"name":"${part.name}"},`;
                            // console.log(sub_part_value);
                        })
                        data.parentBackbone.forEach(backbone => {
                            sub_part_value = sub_part_value + `{"name":"${backbone.name}"},`;
                        })
                        // let sub_backbone_obj = JSON.parse(sub_backbone_value);

                        data.parentPlasmid.forEach(part => {
                            sub_part_value = sub_part_value + `{"name":"${plasmid.name}"},`
                        })
                        // let sub_plasmid_obj = JSON.parse(sub_plasmid_value);
                        data.parentInfo.Part.forEach(part => {
                            sub_part_value = sub_part_value + `{"name":"${part}"},`
                        })

                        data.parentInfo.Backbone.forEach(backbone => {
                            sub_part_value = sub_part_value + `{"name":"${backbone}"},`
                        })

                        data.parentInfo.Plasmid.forEach(plasmid => {
                            sub_part_value = sub_part_value + `{"name":${plasmid}},`
                        })

                        sub_part_value = sub_part_value.substring(0,sub_part_value.length-1);
                        json_value = json_value + sub_part_value + "]}";
                        // let sub_list = [sub_part_obj, sub_backbone_obj, sub_plasmid_obj];
                        // json_obj.children = sub_list;

                        // let newJsonstr = JSON.stringify(json_obj);
                        // console.log(json_value);
                        // console.log(JSON.parse(json_value));
                        return JSON.parse(json_value);
                        // return JSON.parse(json_value);
                    }
                    else{
                        alert(data.message);
                        return null;
                    }

            }
            catch{
                alert("Failed to fetch parent information");
                return null;
            }
        }

        async function getNodeDetailUrl(nodeData){
            const nodeType = (nodeData.type || '').toLowerCase();
            const nodeName = (nodeData.name || '').trim();
            const endpointMap = {
                part: {
                    api: '/WebDatabase/PartID?name=',
                    idKey: 'PartID',
                    detailPrefix: '/LabDatabase/part/'
                },
                backbone: {
                    api: '/WebDatabase/BackboneID?name=',
                    idKey: 'BackboneID',
                    detailPrefix: '/LabDatabase/backbone/'
                },
                plasmid: {
                    api: '/WebDatabase/PlasmidID?name=',
                    idKey: 'PlasmidID',
                    detailPrefix: '/LabDatabase/plasmid/'
                }
            };

            const config = endpointMap[nodeType];
            if (!config || !nodeName) {
                return null;
            }

            const response = await fetch(`${config.api}${encodeURIComponent(nodeName)}`, {
                method: 'GET',
                credentials: 'include'
            });
            if (!response.ok) {
                return null;
            }

            const data = await response.json();
            const targetId = data[config.idKey];
            if (!targetId) {
                return null;
            }

            return `${config.detailPrefix}${targetId}`;
        }

        async function setupEventListeners(){
            chart.on('click', async function(params){
                if(params.componentType === 'series' && params.seriesType === 'tree'){
                    const nodeData = params.data || {};
                    console.log('Clicked node:', nodeData.name);
                    console.log('Clicked node depth:', nodeData.depth);
                    console.log('Clicked node type:', nodeData.type);

                    const detailUrl = await getNodeDetailUrl(nodeData);
                    if (detailUrl) {
                        window.location.href = detailUrl;
                    } else {
                        alert('Unable to find detail page for this node');
                    }
                }
            });
        }
