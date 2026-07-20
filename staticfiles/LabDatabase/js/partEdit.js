document.addEventListener('DOMContentLoaded', function() {
            // 获取DOM元素
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            const saveBtn = document.getElementById('save-btn');
            const cancelBtn = document.getElementById('cancel-btn');
            const sequenceTextarea = document.getElementById('sequence');
            const sequenceContentPreview = document.querySelector('.StartScar');
            const sequenceStartScarPreview = document.querySelector('.StartScar');
            const sequenceEndScarPreview = document.querySelector('.EndScar');
            // const elementSizeInput = document.getElementById('element-size');
            
            // 更新序列预览
            function updateSequencePreview() {
                var partType = document.getElementById("element-type").value;
                
                if(partType === "Promoter"){
                    sequenceStartScarPreview.textContent = "GTGC";
                    sequenceEndScarPreview.textContent = "ATCA";
                }
                else if(partType === "Terminator"){
                    sequenceStartScarPreview.textContent = "TAAA";
                    sequenceEndScarPreview.textContent = "CCTC";
                }
                else if(partType === "RBS"){
                    sequenceStartScarPreview.textContent = "ATCA";
                    sequenceEndScarPreview.textContent = "AATG";
                }
                else if(partType === "CDS"){
                    sequenceStartScarPreview.textContent = "AATG";
                    sequenceEndScarPreview.textContent = "TAAA";
                }
                else if(partType === "P+R"){
                    sequenceStartScarPreview.textContent = "GTGC";
                    sequenceEndScarPreview.textContent = "AATG";
                }

                const sequence = sequenceTextarea.value;
                sequenceContentPreview.textContent = sequence;
                
                // 更新元件大小
                // const cleanSequence = sequence.replace(/\s/g, '');
                // elementSizeInput.value = cleanSequence.length;
            }
            
            // 初始化序列预览
            updateSequencePreview();
            
            // 监听序列变化
            sequenceTextarea.addEventListener('input', updateSequencePreview);
            
            // 保存按钮点击事件
            saveBtn.addEventListener('click', function() {
                // 收集表单数据
                var partid = document.getElementById("gene-id").innerText.split(": ")[1];
                console.log(partid);
                const formData = {
                    elementId: partid,
                    geneName: document.getElementById('name').value,
                    geneAlias:document.getElementById('gene-alias').value,
                    elementType: document.getElementById('element-type').value,
                    speciesSource: document.getElementById('species-source').value || '',
                    elementSize: document.getElementById('sequence').value.length,
                    notes: document.getElementById('notes').value || '',
                    sequence: document.getElementById('sequence').value,
                    references: document.getElementById('references').value || ''
                };
                
                // 模拟保存操作
                // console.log('保存基因元件信息:', formData);
                fetch(`/LabDatabase/modifypart/${partid}`,{
                    method:"POST",
                    body:JSON.stringify(formData),
                    headers:{
                        'X-CSRFToken':csrfToken,
                        'Content-Type':"application/json",
                    }
                })
                // .then(async response => {
                //     const data = await response.json();
                //     return { status: response.status, data: data };
                // })
                .then(response => response.json())
                .then(result =>{
                    const data = result.data;
                    if(data.success){
                        alert("更新成功");
                        window.history.back();
                    }
                    else{
                        alert(data.message);
                    }
                });
                // 更新状态提示
                const statusBadge = document.querySelector('.status-badge');
                statusBadge.textContent = '已更新';
                statusBadge.className = 'status-badge status-updated';
                
            });
            
            // 取消按钮点击事件
            cancelBtn.addEventListener('click', function() {
                if (confirm('确定要取消编辑吗？所有未保存的更改将会丢失。')) {
                    // 模拟返回上一页
                    window.history.back();
                }
            });
            
            // 自动调整序列文本域高度
            function autoResizeTextarea(textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = (textarea.scrollHeight) + 'px';
            }
            
            // 为所有文本域添加自动高度调整
            const textareas = document.querySelectorAll('textarea');
            textareas.forEach(textarea => {
                textarea.addEventListener('input', function() {
                    autoResizeTextarea(this);
                });
                // 初始化调整
                autoResizeTextarea(textarea);
            });
        });
