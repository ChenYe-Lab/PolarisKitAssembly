document.addEventListener('DOMContentLoaded', function() {
            // 获取DOM元素
            const saveBtn = document.getElementById('save-btn');
            const cancelBtn = document.getElementById('cancel-btn');
            const previewBtn = document.getElementById('preview-btn');
            const vectorSequence = document.getElementById('vector-sequence');
            const sequencePreview = document.getElementById('sequence-preview');
            const vectorSizeInput = document.getElementById('vector-size');
            

            
            
            // 更新序列预览
            function updateSequencePreview() {
                const sequence = vectorSequence.value;
                if (sequence.trim() === '') {
                    sequencePreview.textContent = '载体序列待输入...';
                    return;
                }
                
                sequencePreview.textContent = sequence;
                
                
            }
            
            // 初始化序列预览
            updateSequencePreview();
            
            // 监听序列变化
            vectorSequence.addEventListener('input', updateSequencePreview);
            
            // 保存按钮点击事件
            saveBtn.addEventListener('click', function() {
                // 收集表单数据
                const formData = {
                    vectorId: document.getElementById('id-div').innerText.split(": ")[1],
                    vectorName: document.getElementById('vector-name').value,
                    vectorAlias:document.getElementById('vector-alias').value,
                    copyNumber: document.getElementById('copy-number').value || '',
                    host: document.getElementById('host').value || '',
                    notes: document.getElementById('vector-notes').value,
                    scarSites: {
                        BsmBI: document.querySelector('.scar-table tr:nth-child(1) input').value,
                        BsaI: document.querySelector('.scar-table tr:nth-child(2) input').value,
                        BbsI: document.querySelector('.scar-table tr:nth-child(3) input').value,
                        Aari: document.querySelector('.scar-table tr:nth-child(4) input').value,
                        Sapi: document.querySelector('.scar-table tr:nth-child(5) input').value
                    },
                    sequence: document.getElementById('vector-sequence').value || ''
                };
                const ori_input = document.querySelectorAll('#ori-div input[type="text"]');
                const ori_textValue = Array.from(ori_input).map(input => input.value);
                formData.ori = ori_textValue;
                const marker_input = document.querySelectorAll('#marker-div input[type="text"]');
                const marker_textValue = Array.from(marker_input).map(input => input.value);
                formData.marker = marker_textValue;
                const vectorId = document.getElementById('id-div').innerText.split(": ")[1];
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                // 模拟保存操作
                fetch(`/LabDatabase/modifybackbone/${vectorId}`,{
                    method:"POST",
                    body:JSON.stringify(formData),
                    headers:{
                        'X-CSRFToken': csrfToken,
                        'Content-Type':"application/json",
                    }
                })
                .then(response => response.json())
                    // const data = await response.json();
                    // return { status: response.status, data: data };
                .then(data => {
                    // if(result.status === 409){
                    //     alert("名称已存在，请更换名称");
                    //     return;
                    // }
                    // const data = result.data;
                    if(data.success){
                        alert("更新成功");
                        window.history.back();
                    }
                    else{
                        alert(data.message);
                    }
                })
                
                // 更新状态提示
                const statusBadge = document.querySelector('.status-badge');
                statusBadge.textContent = '已更新';
                statusBadge.className = 'status-badge status-updated';
                
                
                
                // 显示成功消息
                // alert(`载体骨架 ${formData.vectorId} 信息已保存成功！`);
            });
            
            
            // 取消按钮点击事件
            cancelBtn.addEventListener('click', function() {
                if (confirm('确定要取消编辑吗？所有未保存的更改将会丢失。')) {
                    // 模拟返回上一页
                    window.history.back();
                }
            });
            
            
            
            // 自动调整文本域高度
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
        function removesubform(buttonElement){
            const subformgroup = buttonElement.closest('.sub-form-group');
            if(subformgroup){
                subformgroup.remove();
            }
        }

        function addorigin(){
            const origin_sub_form = document.createElement('div');
            origin_sub_form.setAttribute("class","sub-form-group");
            origin_sub_form.innerHTML = `
            <input type="text" id="marker-gene" class="form-control" placeholder="请输入复制起点名称">
            <button type="button" class="btn btn-secondary" id="removeMarkerButton" onclick="removesubform(this)"><i class="fa-solid fa-xmark"></i></button>
            `
            const OriDiv = document.getElementById("ori-div");
            OriDiv.appendChild(origin_sub_form);
        }

        function addmarker(){
            const marker_sub_form = document.createElement('div');
            marker_sub_form.setAttribute("class","sub-form-group");
            marker_sub_form.innerHTML = `
            <input type="text" id="marker-gene" class="form-control" placeholder="请输入抗性基因名称">
            <button type="button" class="btn btn-secondary" id="removeMarkerButton" onclick="removesubform(this)"><i class="fa-solid fa-xmark"></i></button>
            `
            const MarkerDiv = document.getElementById("marker-div");
            MarkerDiv.appendChild(marker_sub_form);
        }
