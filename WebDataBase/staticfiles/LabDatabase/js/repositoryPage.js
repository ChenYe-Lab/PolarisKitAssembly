// 获取DOM元素
        const assembleBtn = document.getElementById('assemble-btn');
        const btnText = document.getElementById('btn-text');
        const loadingSpinner = document.getElementById('loading-spinner');
        const diagramPlaceholder = document.getElementById('diagram-placeholder');
        const diagramImage = document.getElementById('diagram-image');
        const notification = document.getElementById('notification');
        const progress = document.getElementById('progress');
        const expiryDate = document.getElementById('expiry-date');
        const expiryStatus = document.getElementById('expiry-status');


        document.addEventListener('DOMContentLoaded', function() {
            
            
            assembleBtn.addEventListener('click', assembleFunction);
            
            
            fetch(`/LabDatabase/RepositoryDiagram/${document.getElementById("repositoryName").innerText}`)
            .then(response => {
                console.log(response);
                if(response != "False"){
                    diagramPlaceholder.style.display = 'none';
                    diagramImage.src = response.url;
                    diagramImage.alt = "质粒示意图";
                    diagramImage.style.display = 'block';
                }
            })


                // 模拟示意图点击放大功能
            diagramImage.addEventListener('click', function() {
                if (this.style.display === 'block') {
                    const originalSrc = this.src;
                    const overlay = document.createElement('div');
                    overlay.style.position = 'fixed';
                    overlay.style.top = '0';
                    overlay.style.left = '0';
                    overlay.style.width = '100%';
                    overlay.style.height = '100%';
                    overlay.style.backgroundColor = 'rgba(0,0,0,0.8)';
                    overlay.style.zIndex = '2000';
                    overlay.style.display = 'flex';
                    overlay.style.justifyContent = 'center';
                    overlay.style.alignItems = 'center';
                    overlay.style.cursor = 'pointer';
                    
                    const enlargedImg = document.createElement('img');
                    enlargedImg.src = originalSrc;
                    enlargedImg.style.maxWidth = '90%';
                    enlargedImg.style.maxHeight = '90%';
                    enlargedImg.style.boxShadow = '0 0 30px rgba(255,255,255,0.1)';
                    enlargedImg.style.borderRadius = '8px';
                    
                    overlay.appendChild(enlargedImg);
                    document.body.appendChild(overlay);
                    
                    overlay.addEventListener('click', function() {
                        document.body.removeChild(overlay);
                    });
                }
            });
            
            // 添加一些动态效果到元件项
            const componentItems = document.querySelectorAll('.component-item');
            componentItems.forEach((item, index) => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(20px)';
                item.style.transition = `opacity 0.5s ease ${index * 0.1}s, transform 0.5s ease ${index * 0.1}s`;
                
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, 100);
            });
        });


            // 组装按钮点击事件
            async function assembleFunction() {
                // 显示加载状态
                btnText.textContent = '组装中...';
                loadingSpinner.style.display = 'inline-block';
                assembleBtn.disabled = true;

                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

                const response = await fetch('/LabDatabase/AssemblyRepo',{
                    method: "POST",
                    headers:{
                        'Content-Type':'application/json',
                        'X-CSRFToken':csrfToken,
                    },
                    body: JSON.stringify({"repositoryName":document.getElementById("repositoryName").innerText}),
                });

                const result = await response.json();

                if(result.task_id){
                    alert(result.message);
                    pollAssemblyTaskStatus(result.task_id,document.getElementById("repositoryName").innerText);
                    // 更新按钮状态
                }
                else{
                    displayResult(result);
                }
            }

            async function pollAssemblyTaskStatus(task_id, repositoryName){
                const pollInterval = setInterval(async () => {
                    try{
                        const response = await fetch(`/LabDatabase/task_status/${task_id}`);
                        const result = await response.json();

                        if(result.status === "completed"){
                            clearInterval(pollInterval);
                            displayResult(result);
                            btnText.textContent = '组装完成';
                            loadingSpinner.style.display = 'none';
            
                            diagramPlaceholder.style.display = 'none';
                            diagramImage.src = `/LabDatabase/RepositoryDiagram/${repositoryName}`;
                            diagramImage.alt = "质粒示意图";
                            diagramImage.style.display = 'block';
                            // 模拟生成示意图
                            diagramImage.onload = function() {
                            // 添加一些动画效果
                                diagramImage.style.opacity = '0';
                                diagramImage.style.transition = 'opacity 0.8s ease';
                            }
                        }
                        else if(result.status === "failed"){
                            clearInterval(pollInterval);
                            displayError(result.message);
                        }
                    }
                    catch(error){
                        clearInterval(pollInterval);
                        displayError('轮询失败: '+error.message);
                    }
                }, 2000);
            }


            function displayError(message){
                alert(message);
            }

            function displayResult(result){
                if(result.status === "completed"){
                    if(result.message){
                        alert(result.message);
                    }
                    else{
                        alert("上传完成");
                    }
                }
                else{
                    alert("处理失败: "+result.message);
                }
            }