        const itemsPerPage = 10;
            let currentPages = {
            part: 1,
            backbone: 1,
            plasmid: 1
        };

        function renderRelatedSummary(item) {
            const parts = Array.isArray(item.related_parts) ? item.related_parts : [];
            const backbones = Array.isArray(item.related_backbones) ? item.related_backbones : [];
            const plasmids = Array.isArray(item.related_plasmids) ? item.related_plasmids : [];
            const sections = [];

            if (parts.length > 0) {
                sections.push(`Part: ${parts.join(', ')}`);
            }
            if (backbones.length > 0) {
                sections.push(`Backbone: ${backbones.join(', ')}`);
            }
            if (plasmids.length > 0) {
                sections.push(`Plasmid: ${plasmids.join(', ')}`);
            }

            return sections.length > 0 ? sections.join('<br>') : '-';
        }

        function ensureArray(value) {
            if (Array.isArray(value)) {
                return value;
            }
            if (typeof value === 'string' && value.trim() !== '') {
                return value.split(',').map(item => item.trim()).filter(Boolean);
            }
            return [];
        }
        
        document.getElementById('uploadBtnPart').addEventListener('click', function() {
                // alert('上传功能将在实际系统中实现');
                const uploadModal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
                var file_input = document.getElementById("fileInput");
                // var files = file_input.files;
                var files = file_input.files;
                uploadModal.hide();
                UploadFile(files, "part");
        });


        
        document.getElementById('uploadBtnBackbone').addEventListener('click', function() {
                // alert('上传功能将在实际系统中实现');
                const uploadModal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
                var file_input = document.getElementById("fileInput");
                var files = file_input.files;
                uploadModal.hide();
                UploadFile(files, "backbone");
            });


            document.getElementById('uploadBtnPlasmid').addEventListener('click', function() {
                // alert('上传功能将在实际系统中实现');
                const uploadModal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
                var file_input = document.getElementById("fileInput");
                console.log(file_input.files);
                var files = file_input.files;
                uploadModal.hide();
                UploadFile(files, "plasmid");
            });
            
            document.getElementById('batchUploadBtn').addEventListener('click', function() {
                var file_input = document.getElementById('batchFileInput');
                console.log(file_input);
                console.log(file_input.files);
                var file = file_input.files;
                batchUploadFile(file);
                const batchUploadModal = bootstrap.Modal.getInstance(document.getElementById('batchUploadModal'));
                batchUploadModal.hide();
            });

            document.getElementById('saveCustomScarBtn').addEventListener('click', async function() {
                const scarName = document.getElementById('customScarName').value.trim();
                const scarSequence = document.getElementById('customScarSequence').value.trim();
                const scarDescription = document.getElementById('customScarDescription').value.trim();

                if (!scarName || !scarSequence) {
                    alert('Scar 名称和碱基序列不能为空');
                    return;
                }

                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                const response = await fetch('/LabDatabase/CustomScar', {
                    method: 'POST',
                    body: JSON.stringify({
                        scar_name: scarName,
                        scar_sequence: scarSequence,
                        scar_description: scarDescription
                    }),
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                });
                const result = await response.json();
                if (result.success) {
                    document.getElementById('customScarForm').reset();
                    const customScarModal = bootstrap.Modal.getInstance(document.getElementById('customScarModal'));
                    customScarModal.hide();
                    alert('自定义 Scar 保存成功');
                }
                else {
                    alert(result.message || '自定义 Scar 保存失败');
                }
            });

            document.getElementById('Format-Checker-button').addEventListener('click',function(){
                var file_input = document.getElementById("Format-Checker");
                var file = file_input.files;
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                const fd = new FormData();
                fd.append('file',file[0]);
                fetch('/LabDatabase/CheckAndFixGenBank',{
                    method:'POST',
                    body:fd,
                    headers:{
                        'X-CSRFToken':csrfToken,
                    }
                }).then(response => response.json())
                .then(data =>{
                    if(data["success"]){
                        var issus_num = data["issue_count"];
                        var changed = data["changed"];
                        window.location.href = `/LabDatabase/getDocByAdd?address=${data["file_path"]}`;
                    }
                    else{
                        displayError("Error");
                    }
                })
            })

            async function UploadFile(files, type){
                if(! files){
                    alert('请选择上传文件');
                    return;
                }
                let fd = new FormData();
                console.log(files.length);
                for (let i = 0;i<files.length;i++){
                    let file = files[i];
                    fd.append('files',file);
                }
                console.log(fd['files'])
                fd.append('type',type);
                const saveFeatureInput = document.getElementById('saveFeatureInput');
                fd.append('save_feature', saveFeatureInput && saveFeatureInput.checked ? 'true' : 'false');
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                const response = await fetch("/LabDatabase/UploadMap",{
                    method:'POST',
                    body:fd,
                    headers:{
                        'X-CSRFToken':csrfToken,
                    }
                });
                var file_input = document.getElementById("fileInput");
                file_input.innerText = "";
                const result = await response.json();
                if(result.task_id){
                    alert(result.message);
                    pollTaskStatus(result.task_id);
                }
                else{
                    displayResult(result);
                }
            }

            async function batchUploadFile(file){
                if(!file){
                    alert('请选择文件');
                    return;
                }
                console.log(file);
                const fd = new FormData();
                fd.append('file',file[0]);

                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                const response = await fetch("/LabDatabase/UploadFile",{
                    method:'POST',
                    body: fd,
                    headers:{
                        'X-CSRFToken': csrfToken,
                    }
                });
                var file_input = document.getElementById('batchFileInput');
                file_input.innerText = '';
                const result = await response.json()
                if(result.task_id){
                    alert(result.message);
                    pollTaskStatus(result.task_id);
                }
                else{
                    displayResult(result);
                }
                
            }

            function pollTaskStatus(taskId){
                const pollInterval = setInterval(async () => {
                    try {
                        const response = await fetch(`/LabDatabase/task_status/${taskId}`);
                        const result = await response.json();
                        console.log(result);
                        if(result.status === "completed"){
                            console.log("completed");
                            
                            clearInterval(pollInterval);
                            displayResult(result);
                        }
                        else if(result.status === "failed"){
                            console.log("failed");
                            console.log(result);
                            clearInterval(pollInterval);
                            if(result.error){
                                displayError(result.error);
                            }
                            else{
                                if(result.message){
                                    displayError(result.message);
                                }
                            }
                        }
                    }
                    catch(error){
                        clearInterval(pollInterval);
                        displayError('轮询失败：'+error.message);
                    }
                }, 2000);
            }

            function displayError(message){
                alert(message);
            }

            function displayResult(result){
                if(result.status === "completed"){
                    if(result.message){
                        if(result.error){
                            if(result.error.length && result.error.length != 0){
                                alert(result.error.join(","));
                            }
                            else{
                                alert(result.message);
                            }
                        }
                        else{
                            displayError(result.message);
                        }
                        
                        
                    }
                    else{
                        if(result.error && result.error.length != 0){
                            alert(result.error.join(","));
                        }
                        else{
                            alert("上传完成");
                        }
                    }
                }
                else{
                    console.log(result.error);
                    alert('处理失败：'+result.error);
                }
            }
            document.getElementById('PartSelectorReset').addEventListener('click', function(){
                const PartTypeSelect = document.getElementById('PartTypeSelect');
                const PartEnzyme = document.getElementById('PartEnzyme');
                const PartScar = document.getElementById('PartScar');
                PartTypeSelect.selectedIndex = 0;
                PartEnzyme.selectedIndex = 0;
                PartScar.selectedIndex = 0;
            });

            document.getElementById('BackboneSelectorReset').addEventListener('click', function(){
                const OriSelect = document.getElementById('OriSelect');
                const MarkerSelect = document.getElementById('MarkerSelect');
                const BackboneEnzyme = document.getElementById('BackboneEnzyme');
                const BackboneScar = document.getElementById('BackboneScar');
                OriSelect.selectedIndex = 0;
                MarkerSelect.selectedIndex = 0;
                BackboneEnzyme.selectedIndex = 0;
                BackboneScar.selectedIndex = 0;
            });

            document.getElementById('PlasmidSelectorReset').addEventListener('click',function(){
                const OriSelectPlasmid = document.getElementById('OriSelectPlasmid');
                const MarkerSelectPlasmid = document.getElementById('MarkerSelectPlasmid');
                const PlasmidEnzyme = document.getElementById('PlasmidEnzyme');
                const PlasmidScar = document.getElementById('PlasmidScar');
                OriSelectPlasmid.selectedIndex = 0;
                MarkerSelectPlasmid.selectedIndex = 0;
                PlasmidEnzyme.selectedIndex = 0;
                PlasmidScar.selectedIndex = 0;
            });

            //搜索功能实现
            //part
            document.getElementById('Partsearchbutton').addEventListener('click', function() {
                let Type = document.getElementById('PartTypeSelect').options[document.getElementById('PartTypeSelect').selectedIndex].text;
                let Enzyme = document.getElementById('PartEnzyme').options[document.getElementById('PartEnzyme').selectedIndex].text;
                let Scar = document.getElementById('PartScar').options[document.getElementById('PartScar').selectedIndex].text;
                let name = document.getElementById('PartSearchInput').value;
                if(Type == "" && Enzyme == "" && Scar == "" && name == ""){
                    alert("请选择筛选标准");
                    return
                }
                else{
                    renderTable("part",true,1);
                }
            });
            //Backbone
            document.getElementById('Backbonesearchbutton').addEventListener('click', function() {
                let ori = document.getElementById('OriSelect').options[document.getElementById('OriSelect').selectedIndex].text;
                let marker = document.getElementById('MarkerSelect').options[document.getElementById('MarkerSelect').selectedIndex].text;
                let Enzyme = document.getElementById('BackboneEnzyme').options[document.getElementById('BackboneEnzyme').selectedIndex].text;
                let scar = document.getElementById("BackboneScar").options[document.getElementById("BackboneScar").selectedIndex].text;
                let name = document.getElementById("BackboneSearchInput").value;
                if(ori == "" && marker == "" && Enzyme == "" && scar == "" && name == ""){
                    alert("请选择筛选标准");
                }
                else{
                    renderTable("backbone",true,1);
                }
            });
            //Plasmid
            document.getElementById('Plasmidsearchbutton').addEventListener('click',function(){
                let ori = document.getElementById('OriSelectPlasmid').options[document.getElementById('OriSelectPlasmid').selectedIndex].text;
                let marker = document.getElementById('MarkerSelectPlasmid').options[document.getElementById('MarkerSelectPlasmid').selectedIndex].text;
                let Enzyme = document.getElementById('PlasmidEnzyme').options[document.getElementById('PlasmidEnzyme').selectedIndex].text;
                let scar = document.getElementById("PlasmidScar").options[document.getElementById("PlasmidScar").selectedIndex].text;
                let name = document.getElementById("PlasmidSearchInput").value;
                console.log("testtest");
                if(ori == "" && marker == "" && Enzyme == "" && scar == "" && name == ""){
                    alert("请选择筛选标准");
                }
                else{
                    renderTable("plasmid",true,1);
                }
            });








function toggleMenu(menuHeader){
                const menuItem = menuHeader.parentElement;
                const submenu = menuItem.querySelector('.submenu');
                const arrow = menuHeader.querySelector('.menu-arrow i');
    
            // 切换子菜单
            submenu.classList.toggle('expanded');
    
            // 切换箭头方向
            if (submenu.classList.contains('expanded')) {
                arrow.classList.remove('fa-angle-down');
                arrow.classList.add('fa-angle-up');
                menuHeader.classList.add('active');
            } else {
                arrow.classList.remove('fa-angle-up');
                arrow.classList.add('fa-angle-down');
                menuHeader.classList.remove('active');
            }
            // 关闭其他展开的菜单（可选）
            closeOtherMenus(menuItem);
        }


        function toggleSubMenu(submenuHeader) {
    const menuItem = submenuHeader.parentElement;
    const subSubmenu = menuItem.querySelector('.sub-submenu');
    const arrow = submenuHeader.querySelector('.menu-arrow i');
    
    // 切换三级子菜单
    subSubmenu.classList.toggle('expanded');
    
    // 切换箭头方向
    if (subSubmenu.classList.contains('expanded')) {
        arrow.classList.remove('fa-angle-right');
        arrow.classList.add('fa-angle-down');
        submenuHeader.classList.add('active');
    } else {
        arrow.classList.remove('fa-angle-down');
        arrow.classList.add('fa-angle-right');
        submenuHeader.classList.remove('active');
    }
}

// 关闭其他菜单
function closeOtherMenus(currentMenuItem) {
    const allMenuItems = document.querySelectorAll('.menu-item');
    
    allMenuItems.forEach(item => {
        if (item !== currentMenuItem) {
            const submenu = item.querySelector('.submenu');
            const header = item.querySelector('.menu-header');
            const arrow = header ? header.querySelector('.menu-arrow i') : null;
            
            if (submenu && submenu.classList.contains('expanded')) {
                submenu.classList.remove('expanded');
                
                if (arrow) {
                    arrow.classList.remove('fa-angle-up');
                    arrow.classList.add('fa-angle-down');
                }
                
                if (header) {
                    header.classList.remove('active');
                }
            }
        }
    });
}



function setupMenuEvents() {
    // 主菜单项点击
    const menuHeaders = document.querySelectorAll('.menu-header');
    menuHeaders.forEach(header => {
        header.addEventListener('click', function(e) {
            toggleMenu(this);
            e.stopPropagation();
        });
    });
    
    // 子菜单头部点击
    const submenuHeaders = document.querySelectorAll('.submenu-header');
    submenuHeaders.forEach(header => {
        header.addEventListener('click', function(e) {
            toggleSubMenu(this);
            e.stopPropagation();
        });
    });
    
    // 菜单项链接点击
    const menuItems = document.querySelectorAll('.submenu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // 移除所有active类
            menuItems.forEach(i => i.classList.remove('active'));
            
            // 添加active类到当前项
            this.classList.add('active');
            
            // 获取工具类型
            const tool = this.getAttribute('data-tool');
            
            // 执行相应的工具函数
            if (tool) {
                switchTool(tool);
            }
            
            e.stopPropagation();
        });
    });
    
    // 点击外部关闭菜单（移动端）
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.sidebar');
            const isClickInsideSidebar = sidebar.contains(e.target);
            
            if (!isClickInsideSidebar) {
                sidebar.classList.remove('active');
            }
        }
    });
}
            // 侧边栏（展开）切换
            // sidebarToggle.addEventListener('click', () => {
            //     sidebar.classList.toggle('collapsed');
            //     mainContent.classList.toggle('sidebar-collapsed');
                
            //     console.log("siderToggle click!");
            //     // 切换按钮图标
            //     const icon = sidebarToggle.querySelector('i');
            //     if (sidebar.classList.contains('collapsed')) {
            //         icon.className = 'fas fa-bars';
            //     } else {
            //         icon.className = 'fas fa-times';
            //     }
            // });
            // //===================================================================================
            // // 侧边栏菜单项点击事件
            // menuHeader.forEach(item => {
            //     item.addEventListener('click', function() {
            //         this.classList.toggle('active');
                    
            //         const submenu = this.nextElementSibling;
            //         if(submenu.classList.contains('open')){
            //             submenu.classList.remove('open');
            //         }
            //         else{
            //             document.querySelectorAll('.submenu.open').forEach(openMenu =>{
            //                 if(openMenu != submenu){
            //                     openMenu.classList.remove('open');
            //                     openMenu.previousElementSibling.classList.remove('active');
            //                 }
            //             });
            //             submenu.classList.add('open');
            //         }
            //     });
            // });

            // submenuHeader.forEach(item =>{
            //     item.addEventListener('click',function(){
            //         this.classList.toggle("active");
            //         const sub_submenu = this.nextElementSibling;

            //         if(sub_submenu.classList.contains('open')){
            //             sub_submenu.classList.remove('open');
            //         }
            //         else{
            //             document.querySelectorAll('.sub_submenu.open').forEach(openMenu =>{
            //                 if(openMenu != sub_submenu){
            //                     openMenu.classList.remove('open');
            //                     openMenu.previousElementSibling.classList.remove('active');
            //                 }
            //             });
            //             sub_submenu.classList.add('open');
            //         }
            //     });
            // });



            
            // const submenuItems = document.querySelectorAll('.submenu-item');
            // submenuItems.forEach(item => {
            //     item.addEventListener('click',function(e){
            //         submenuItems.forEach(i => i.classList.remove('active'));
            //         this.classList.add('active');
            //         e.preventDefault();

            //         // const menuText = this.textContent;
            //         // const parentMenu = this.closet('.menu-item').querySelector('.menu-text').textContent;
            //         const tool = item.getAttribute('data-tool');
            //         switchTool(tool);
            //     })
            // });

            // 工具切换函数
            function switchTool(tool) {
                const pageTitle = document.querySelector('.card-title');
                // const pageDesc = document.querySelector('.page-title p');
                
                switch(tool) {
                    case 'EcoliDatabase':
                        pageTitle.textContent = '大肠杆菌生物元件仓库';
                        // pageDesc.textContent = '搜索、管理和分享合成生物学元件，加速您的研究与开发';
                        showRepositoryContent();
                        break;
                    case 'YeastDatabase':
                        pageTitle.textContent = '酵母生物元件仓库';
                        // pageDesc.textContent = '搜索、管理和分享合成生物学元件，加速您的研究与开发';
                        showRepositoryContent();
                        break;
                    case 'MammaliaDatabase':
                        pageTitle.textContent = '哺乳动物生物元件仓库';
                        // pageDesc.textContent = '搜索、管理和分享合成生物学元件，加速您的研究与开发';
                        showRepositoryContent();
                        break;
                    case 'base-designer':
                        showBaseDesigner();
                        break;
                    // case 'color_designer':
                    //     pageTitle.textContent = '颜色设计工具';
                    //     pageDesc.textContent = '根据需求颜色设计工具';
                    //     showColorDesignContent();
                    //     break;
                    case 'logic_designer':
                        showLogicDesignToolsContent();
                        break;
                    case 'create_repo':
                        create_repo();
                        break;
                    case 'create_plate':
                        create_plate();
                        break;
                }
            }

            // 显示不同工具的内容
            // 搜索界面显示
            function showRepositoryContent() {
                // 显示默认的搜索界面
                document.querySelector('.main-content').style.display = 'block';
                document.querySelector('.base-design-container').style.display = 'none';
                // document.querySelector('.color-design-container').style.display = 'none';
                document.querySelector('.Logic-designer-container').style.display = 'none';
            }
            //基础设计界面显示
            function showBaseDesigner(){
                console.log("showBaseDesigner");
                document.querySelector('.main-content').style.display = 'none';
                document.querySelector('.base-design-container').style.display = 'block';
                // document.querySelector('.color-design-container').style.display = 'none';
                document.querySelector('.Logic-designer-container').style.display = 'none';
            }

            //颜色设计界面显示
            // function showColorDesignContent(){
            //     document.querySelector('.search-container').style.display = 'none';
            //     document.querySelector('.base-design-container').style.display = 'none';
            //     // document.querySelector('.color-design-container').style.display = 'block';
            //     document.querySelector('.Logic-designer-container').style.display = 'none';
            // }

            //逻辑门界面显示
            function showLogicDesignToolsContent() {
                document.querySelector('.main-content').style.display = 'none';
                document.querySelector('.base-design-container').style.display = 'none';
                // document.querySelector('.color-design-container').style.display = 'none';
                document.querySelector('.Logic-designer-container').style.display = 'block';
            }












        // 初始化页面
        document.addEventListener('DOMContentLoaded', function() {

            document.addEventListener('click',function(event){
                const userCards = document.querySelectorAll('.user-card');

                userCards.forEach(card => {
                    const cardContent = card.querySelector('.user-info-card');
                    const usernameLink = card.querySelector('.username-link');

                    if(!card.contains(event.target) && cardContent.style.visibility === 'visible'){
                        cardContent.style.opacity = '0';
                        cardContent.style.visibility = 'hidden';
                        cardContent.style.transform = 'translateY(10px)';
                    }
                })
            });

            const infoCards = document.querySelectorAll('.user-info-card');
            infoCards.forEach(card => {
                card.addEventListener('click', function(event) {
                    event.stopPropagation();
                });
            });
            
            // 添加卡片显示/隐藏的动画延迟效果（可选）
            const usernameLinks = document.querySelectorAll('.username-link');
            usernameLinks.forEach(link => {
                link.addEventListener('mouseenter', function() {
                    console.log("aaaaaaaaaa");
                    const card = this.closest('.user-card').querySelector('.user-info-card');
                    if (card) {
                        // 清除之前的定时器
                        clearTimeout(card.hideTimer);
                        
                        // 显示卡片
                        card.style.opacity = '1';
                        card.style.visibility = 'visible';
                        card.style.transform = 'translateY(5px)';
                    }
                });
                
                link.addEventListener('mouseleave', function() {
                    const card = this.closest('.user-card').querySelector('.user-info-card');
                    if (card) {
                        // 设置延迟隐藏，防止鼠标移动到卡片上的瞬间隐藏
                        card.hideTimer = setTimeout(() => {
                            card.style.opacity = '0';
                            card.style.visibility = 'hidden';
                            card.style.transform = 'translateY(10px)';
                        }, 100);
                    }
                });
            });
            
            // 卡片本身也需要监听鼠标事件，防止过早隐藏
            infoCards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    clearTimeout(this.hideTimer);
                });
                
                card.addEventListener('mouseleave', function() {
                    this.hideTimer = setTimeout(() => {
                        this.style.opacity = '0';
                        this.style.visibility = 'hidden';
                        this.style.transform = 'translateY(10px)';
                    }, 100);
                });
            });
            // 初始化所有标签页
            
            renderTable('part',false, currentPages.part);
            renderTable('backbone',false,currentPages.backbone);
            renderTable('plasmid',false,currentPages.plasmid);
            
            // 添加上传按钮事件监听

            //渲染selector div
            renderselect();

            

            const sidebar = document.getElementById('sidebar');
            const sidebarToggle = document.getElementById('sidebarToggle');
            const mainContent = document.getElementById('mainContent');
            // const sidebarItems = document.querySelectorAll('.sidebar-item');
            // const menuHeader = document.querySelectorAll('.menu-header');
            // const submenuHeader = document.querySelectorAll(".submenuHeader");
            
            // 侧边栏（展开）切换
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('sidebar-collapsed');
                
                console.log("siderToggle click!");
                // 切换按钮图标
                const icon = sidebarToggle.querySelector('i');
                if (sidebar.classList.contains('collapsed')) {
                    icon.className = 'fas fa-bars';
                } else {
                    icon.className = 'fas fa-times';
                }
            });


            
            // function showToolPlaceholder(title, description) {
            //     let placeholder = document.getElementById('tool-placeholder');
            //     if (!placeholder) {
            //         placeholder = document.createElement('div');
            //         placeholder.id = 'tool-placeholder';
            //         placeholder.style.cssText = `
            //             background-color: white;
            //             border-radius: 10px;
            //             box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            //             padding: 40px;
            //             text-align: center;
            //             margin-top: 20px;
            //         `;
            //         mainContent.appendChild(placeholder);
            //     }
                
            //     placeholder.innerHTML = `
            //         <div style="margin-bottom: 20px;">
            //             <i class="fas fa-cog" style="font-size: 3rem; color: #3498db; margin-bottom: 20px;"></i>
            //         </div>
            //         <h2 style="color: #2c3e50; margin-bottom: 15px;">${title}</h2>
            //         <p style="color: #7f8c8d; font-size: 1.1rem; margin-bottom: 30px;">${description}</p>
            //         <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db;">
            //             <p style="color: #6c757d; margin: 0;"><i class="fas fa-info-circle"></i> 此功能正在开发中，敬请期待...</p>
            //         </div>
            //     `;
            // }

            //===================================================================================
            //右上角用户信息展示
            // validationUser();
            // function validationUser(){
            //     fetch("/myapp/val")
            //     .then(response => response.json())
            //     .then(data => {
            //         console.log(data['username']);
            //         if(data['username'] != ""){
            //             document.getElementById('auth-buttons').style.display = 'none';
            //             document.getElementById('user-info').style.display = 'block';
            //             document.getElementById('username-label').innerHTML = data['username'];
            //         }
            //         else{
            //             document.getElementById('auth-buttons').style.display = 'block';
            //             document.getElementById('user-info').style.display = 'none';
            //         }
            //     })
            //     .catch(error => {
            //         alert(error.message);
            //     });
            // }

            //待开发功能
            // document.getElementById("UserProfileLabel").addEventListener('click',() =>{
            //     alert("打开用户主页");
            // });

            //===================================================================================
            // 登录/注册按钮功能
            // const loginBtn = document.querySelector('.btn-login');
            // const registerBtn = document.querySelector('.btn-register');

            // //登录
            // loginBtn.addEventListener('click', () => {
            //     window.location.href = "/myapp/login";
            // });

            // //注册
            // registerBtn.addEventListener('click', () => {
            //     window.location.href = "/myapp/register";
            // });

            // //退出登录
            // document.getElementById('btn_logout').addEventListener('click', () => {
            //     window.location.href = "/myapp/logout";
            // });


            //===================================================================================
            //搜索功能实现
            // const searchBtn = document.getElementById('search-button');
            // // $('#search-button').on('click',
            // document.getElementById("search-button").addEventListener('click' ,()=>{
            //     // function(){
            //     tool = document.querySelector(".submenu-item.active").getAttribute('data-tool');
            //     console.log(tool);
            //     if(nameSearch.classList.contains('active')){
            //         var NameKeywords = nameSearch.value;
            //         if(NameKeywords == ""){
            //             alert("关键字不能为空");
            //         }
            //         else{
            //             if(tool == "EcoliDatabase"){
            //                 window.location.href = "/myapp/showEcoli?keywords="+NameKeywords;
            //             }
            //             else if(tool == "YeastDatabase"){
            //                 window.location.href = "/myapp/showYeast?keywords="+NameKeywords;
            //             }
            //             else if(tool == "MammaliaDatabase"){
            //                 window.location.href = "/myapp/showMammalia?keywords="+NameKeywords;
            //             }
            //         }
            //     }
            //     else if(sequenceSearch.classList.contains("active")){
            //         var SequenceKeywords = sequenceSearch.value;
            //         if(SequenceKeywords == ""){
            //             alert("关键字不能为空");
            //         }
            //         else{
            //             if(tool == "EcoliDatabase"){
            //                 window.location.href = "/myapp/showEcoliSeq?Seq="+SequenceKeywords;
            //             }
            //             else if(tool == "YeastDatabase"){
            //                 window.location.href = "/myapp/showYeastSeq?Seq="+SequenceKeywords;
            //             }
            //             else if(tool == "MammaliaDatabase"){
            //                 window.location.href = "/myapp/showMammaliaSeq?Seq="+SequenceKeywords;
            //             }
            //         }
                    
            //     }
            // });

            

            //===================================================================================
            //创建仓库功能实现
            const createRepoModal = bootstrap.Modal.getInstance(document.getElementById("modalOverlay-Repo"));
            const cancelBtn = document.getElementById('cancelBtn');
            const confirmBtn = document.getElementById('confirmBtn');
            // const warehouseNameInput = document.getElementById(''warehouseName);
            // const warehouseNoteInput = document.getElementById('warehouseNote');
            const notificationCreateRepo = document.getElementById('notificationCreateRepo');
            const createBtn = document.getElementById('assemblyFileUpload');
            
            //打开弹窗
            createBtn.addEventListener('click', () => {
                var assembly_upload = document.getElementById("AssemblyFileInput");
                var assemblyFile = assembly_upload.files;
                createWarehouse(assemblyFile);
                const createRepoModal = bootstrap.Modal.getInstance(document.getElementById("modalOverlay-Repo"));
                createRepoModal.hide();
                console.log("create repo window");
            });
        
            // // 关闭弹窗
            // function closeModal() {
            //     // modalOverlayRepo.classList.remove('show');
            //     createRepoModal.hide();
            // }
        
            // 取消按钮点击事件
            // cancelBtn.addEventListener('click', closeModal());
        
            // 点击遮罩层关闭弹窗
            // createRepoModal.addEventListener('click', function(e) {
            //     if (e.target === createRepoModal) {
            //         createRepoModal.hide();
            //     }
            // });
        
            // 确认按钮点击事件


            //==========================================================================
            //创建Plate功能及显示弹窗
            const createPlateModal = bootstrap.Modal.getInstance(document.getElementById("modalOverlay-Plate"))
            const cancelBtnPlate = document.getElementById('cancelBtn-Plate');
            // const confirmBtnPlate = document.getElementById('confirmBtn-Plate');
            // const PlateNameInput = document.getElementById('PlateName');
            const notificationCreatePlate = document.getElementById('notificationCreatePlate');
            const modalOverlayPlate_Section = document.getElementById('PlateSection');
            // 创建仓库Plate功能
            const AssemblyStartBtn = document.getElementById('AssemblyStartBtn');
            const BatchAssemblyStartBtn = document.getElementById('BatchAssemblyStartBtn');
            
            const createAssemblyTaskBtn = document.getElementById("create-plate");

            
            fetch('/WebDatabase/getrepos')
            .then(response => response.json())
            .then(data =>{
                console.log(data);
                if(data.success){
                    data.repo.forEach((eachRepo) =>{
                        console.log(eachRepo.name)
                        const repoOption = document.createElement("option");
                        repoOption.innerText=eachRepo.name;
                        modalOverlayPlate_Section.appendChild(repoOption);
                });
                }else{
                    showNotification(data.message || '创建失败',true);
                }
            })
            .catch(error => {
                showNotification("网络错误，请重试",true);
            })
            

            AssemblyStartBtn.addEventListener('click', () => {
                let wareName = modalOverlayPlate_Section.value.trim();
                assemblyStart(wareName);
                const createPlateModal = bootstrap.Modal.getInstance(document.getElementById("modalOverlay-Plate"))
                createPlateModal.hide();
            });

            BatchAssemblyStartBtn.addEventListener('click', () => {
                let wareName = modalOverlayPlate_Section.value.trim();
                assemblyStart(wareName);
                const createPlateModal = bootstrap.Modal.getInstance(document.getElementById("modalOverlay-Plate"))
                createPlateModal.hide();
            });

        
            // 取消按钮点击事件
            // cancelBtnPlate.addEventListener('click', closeModalPlate);
        
            // 点击遮罩层关闭弹窗
            // createPlateModal.addEventListener('click', function(e) {
            //     if (e.target === createPlateModal) {
            //         createPlateModal.hide();
            //     }
            // });
        
            // 确认按钮点击事件
            // confirmBtnPlate.addEventListener('click', function() {
            //     const repositoryName = modalOverlayPlate_Section.value.trim();
            //     // 在实际应用中，这里会调用API创建仓库
            //     createPlate(repositoryName);
            // });
        
            // 按Enter键确认创建
            // PlateNameInput.addEventListener('keypress', function(e) {
            //     if (e.key === 'Enter') {
            //         confirmBtnPlate.click();
            //     }
            // });
            // 创建Plate函数
            // function createPlate(name) {
            // // 模拟API调用
            //     console.log(`创建Plate: ${name}`);
            //     fetch('/WebDatabase/getrepo',{
            //         method: 'POST',
            //         headers:{
            //             'Content-Type':'application/json',
            //         },
            //         body: JSON.stringify({Name:name})
            //     })
            //     .then(response => {
            //         if(response.status == 410){
            //             alert("仓库已过期");
            //         }
            //         return response.json();
            //     })
            //     .then(data => {
            //         if(data.success){
            //             alert("创建成功");
            //             closeModalPlate();
            //             // window.location.href = "/myapp/showPlate?repositoryID="+data.repository;
            //         }
            //         else{
            //             alert(data.message || '创建失败');
            //         }
            //     })
            //     .catch(error => {
            //         alert('网络错误，请重试');
            //     });
            // }
        
            // // 显示通知
            // function showNotificationPlate(message, isError = false) {
            //     notificationCreatePlate.textContent = message;
            
            //     if (isError) {
            //         notificationCreatePlate.classList.add('error');
            //     } else {
            //         notificationCreatePlate.classList.remove('error');
            //     }
            
            //     notificationCreatePlate.classList.add('show');
            
            //     setTimeout(() => {
            //         notificationCreatePlate.classList.remove('show');
            //     }, 3000);
            // }
            

            //基本设计功能表单提交
            const submitBtn = document.getElementById('design-submit');
            if (submitBtn) {
                submitBtn.addEventListener('click', function() {
                    const species = (document.getElementById('design-species') || {}).value || '';
                    const gene = (document.getElementById('design-gene') || document.getElementById('design-gene') || {}).value || '';
                    const expression = (document.getElementById('design-expression') || {}).value || '';

                    if (!species || !gene || !expression) {
                        alert('请完整填写表单');
                        return;
                    }

                    // 这里可替换为真正的提交逻辑（例如fetch到后端接口）
                    alert("代开发");
                    // fetch('/myapp/BasicDesign',{
                    //     method: 'POST',
                    //     headers:{
                    //         'Content-Type':'application/json',
                    //     },
                    //     body: JSON.stringify({species:species,gene:gene,expression:expression})
                    // })
                    // .then(response => response.json())
                    // .then(data => {
                    //     if(data.success){
                    //         //自动创建一个仓库，并且以网页形式返回设计表单
                    //         alert("设计内容！");
                    //     }
                    //     else{
                    //         alert(data.message);
                    //     }
                    // })
                    // .catch(error => {
                    //     alert('网络错误，请重试');
                    // })
                })
            }

        // 获取DOM元素
        const gateOptions = document.querySelectorAll('.gate-option');
        const notParams = document.getElementById('not-params');
        const andParams = document.getElementById('and-params');
        const orParams = document.getElementById('or-params');
        const nandParams = document.getElementById('nand-params');
        const norParams = document.getElementById('nor-params');
        const gateSymbol = document.getElementById('gateSymbol');
        const gateLabel = document.getElementById('gateLabel');
        const saveButtonlog = document.getElementById('saveButtonlog');
        const resetButton = document.getElementById('resetButton');
        const notificationlog = document.getElementById('notificationlog');
        
        // 当前选择的逻辑门类型
        let selectedGate = 'not';
        
        // 逻辑门类型选择事件
        gateOptions.forEach(option => {
            option.addEventListener('click', function() {
                // 移除所有激活状态
                gateOptions.forEach(opt => opt.classList.remove('active'));
                
                // 设置当前为激活状态
                this.classList.add('active');
                
                // 更新选中的逻辑门类型
                selectedGate = this.dataset.gate;
                
                // 更新参数显示
                updateParameterDisplay();
                
                // 更新预览
                updatePreview();
            });
        });
        
        // 更新参数显示
        function updateParameterDisplay() {
            // 隐藏所有参数区域
            notParams.style.display = 'none';
            andParams.style.display = 'none';
            orParams.style.display = 'none';
            nandParams.style.display = 'none';
            norParams.style.display = 'none';
            
            // 显示当前选择的参数区域
            switch(selectedGate) {
                case 'not':
                    notParams.style.display = 'block';
                    break;
                case 'and':
                    andParams.style.display = 'block';
                    break;
                case 'or':
                    orParams.style.display = 'block';
                    break;
                case 'nand':
                    nandParams.style.display = 'block';
                    break;
                case 'nor':
                    norParams.style.display = 'block';
                    break;
            }
        }
        
        // 更新预览
        function updatePreview() {
            let symbol = '';
            let label = '';
            
            switch(selectedGate) {
                case 'not':
                    symbol = 'NOT';
                    label = '非门 - 信号取反';
                    break;
                case 'and':
                    symbol = 'AND';
                    label = '与门 - 所有输入为真时输出为真';
                    break;
                case 'or':
                    symbol = 'OR';
                    label = '或门 - 任一输入为真时输出为真';
                    break;
                case 'nand':
                    symbol = 'NAND';
                    label = '与非门 - 与门的取反';
                    break;
                case 'nor':
                    symbol = 'NOR';
                    label = '或非门 - 或门的取反';
                    break;
            }
            
            gateSymbol.textContent = symbol;
            gateLabel.textContent = label;
        }
        
        // 保存按钮点击事件
        saveButtonlog.addEventListener('click', function() {
            // 收集表单数据
            const gateData = {
                type: selectedGate,
                name: document.getElementById('gateName').value,
                description: document.getElementById('gateDescription').value
            };
        
            // 验证数据
            if (!validateGateData(gateData)) {
                alert('请填写所有必需的参数！');
                return;
            }
        });
        
        // 重置按钮点击事件
        resetButton.addEventListener('click', function() {
            // 重置所有输入字段
            document.querySelectorAll('.input-field').forEach(input => {
                input.value = '';
            });
            
            // 重置为默认值
            document.getElementById('andInputs').value = '2';
            document.getElementById('orInputs').value = '2';
            document.getElementById('nandInputs').value = '2';
            document.getElementById('norInputs').value = '2';
            
            // 重置选择为非门
            gateOptions.forEach(opt => opt.classList.remove('active'));
            document.querySelector('.gate-option[data-gate="not"]').classList.add('active');
            selectedGate = 'not';
            updateParameterDisplay();
            updatePreview();
        });
        
        // 验证逻辑门数据
        function validateGateData(data) {
            if (!data.name || !data.description) {
                return false;
            }
            
            switch(data.type) {
                case 'not':
                    if (!data.YMax || !data.YMin || !data.K) {
                        return false;
                    }
                    break;
                case 'and':
                case 'or':
                case 'nand':
                case 'nor':
                    if (!data.inputs || !data.threshold) {
                        return false;
                    }
                    break;
            }
            return true;
        }
        });

        document.getElementById("admin_index").addEventListener('click', function(){
            window.location.href = "/LabDatabase/adminPage";
        })


            // 组装函数
            async function assemblyStart(warehouseName) {
                if (!warehouseName){
                    alert('请选择仓库名称');
                    return;
                }
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

                const response = await fetch('/LabDatabase/AssemblyRepo',{
                    method : "POST",
                    headers:{
                        'Content-Type':'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({"repositoryName":warehouseName}),
                });
                // .then(response => response.json)
                const result = await response.json();
                console.log(result);
                if(result.task_id){
                    alert(result.message);
                    pollAssemblyTaskStatus(result.task_id,warehouseName);
                }
                else{
                    displayResult(result);
                }
            }

            function pollAssemblyTaskStatus(taskId,warehouseName){
                const pollInterval = setInterval(async () => {
                    try {
                        const response = await fetch(`/LabDatabase/task_status/${taskId}`);
                        const result = await response.json();
                        console.log(result);
                        if(result.status === "completed"){
                            console.log("completed");
                            
                            clearInterval(pollInterval);
                            displayResult(result);

                            // window.location.href = `/LabDatabase/getAssembly/${warehouseName}/${taskId}`
                            window.location.href = result.result.download_url;
                        }
                        else if(result.status === "failed"){
                            console.log("failed");
                            console.log(result);
                            clearInterval(pollInterval);
                            displayError(result.error);
                        }
                    }
                    catch(error){
                        clearInterval(pollInterval);
                        displayError('轮询失败：'+error.message);
                    }
                }, 2000);
            }





        
            // 创建仓库函数
            async function createWarehouse(file) {
                if (!file){
                    alert('请选择文件');
                    return;
                }
                let fd = new FormData();
                console.log(file.length);
                fd.append('file',file[0]);
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

                const response = await fetch('/LabDatabase/createRepo',{
                    method: 'POST',
                    body:fd,
                    headers:{
                        'X-CSRFToken':csrfToken,
                    },
                });
                // .then(response => response.json)
                const result = await response.json();
                if(result.task_id){
                    alert(result.message);
                    pollTaskStatus(result.task_id);
                }
                else{
                    displayResult(result);
                }
            }
        
            // 显示通知
            function showNotification(message, isError = false) {
                notificationCreateRepo.textContent = message;
            
                if (isError) {
                    notificationCreateRepo.classList.add('error');
                } else {
                    notificationCreateRepo.classList.remove('error');
                }
            
                notificationCreateRepo.classList.add('show');
            
                setTimeout(() => {
                    notificationCreateRepo.classList.remove('show');
                }, 3000);
            }

        // 渲染表格
        function renderTable(type,isSearch,page) {
            console.log("renderTable");
            const tableBody = document.getElementById(`${type}TableBody`);
            const pagination = document.getElementById(`${type}Pagination`);
            const paginationInfo = document.getElementById(`${type}PaginationInfo`);
            let result = {};
            let totalItems = 0;
            let totalPages = 0;
            let currentPage = 1;
            let offset = 0;
            //非搜索渲染
            if(isSearch == false){
                if(type === 'part'){
                    fetch(`/LabDatabase/getdata?type=part&page=${page}`)
                    .then(response => response.json())
                    .then(data =>{
                        result = data.data;
                        totalItems = data.pagination.total_count;
                        totalPages = data.pagination.total_pages;
                        currentPage = data.pagination.current_page;
                        offset = data.pagination.offset;
                    
                        tableBody.innerHTML = '';
                        if (totalItems === 0) {
                            tableBody.innerHTML = `
                            <tr>
                                <td colspan="7">
                                    <div class="empty-state">
                                        <div class="empty-icon">📭</div>
                                        <div>没有找到数据</div>
                                    </div>
                                </td>
                            </tr>
                        `;
                        } else {
                        // 填充表格数据
                            result.forEach(item => {
                                const row = document.createElement('tr');
                                let PartType = "";
                                if(item.type === 1){
                                    PartType = "promoter";
                                }
                                else if(item.type === 2){
                                    PartType = "CDS";
                                }
                                else if(item.type === 3){
                                    PartType = "Terminator";
                                }
                                else if(item.type === 4){
                                    PartType = "RBS";
                                }
                                else if(item.type === 5){
                                    PartType = "P+R";
                                }
                                row.setAttribute("id", `part_row_${item.partid}`)
                                row.innerHTML = `
                                    <td>${item.name}</td>
                                    <td>${item.alias}</td>
                                    <td>${PartType}</td>
                                    <td>${item.sourceorganism}</td>
                                    <td>${item.reference}</td>
                                    <td><span class="status-badge ${item.tag === 'normal' ? 'status-active' : 'status-inactive'}">${item.tag === 'normal' ? '正常' : '非正常'}</span></td>
                                    <td class="action-cell">
                                        <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/LabDatabase/part/${item.partid}'">查看</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="window.location.href='/LabDatabase/modifypart/${item.partid}'">编辑</button>
                                        <button class="btn btn-sm btn-outline-danger" onclick = "PartDelete(${item.partid})">删除</button>
                                    </td>
                                `;
                                tableBody.appendChild(row);
                            })
                        }
                        // 更新分页信息
                        paginationInfo.textContent = `显示 ${totalItems} 条记录中的 ${offset} 到 ${offset+10} 条`;
            
                        // 生成分页控件
                        pagination.innerHTML = '';
            
                        // 上一页按钮
                        const prevLi = document.createElement('li');
                        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
                        prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch}, ${page - 1})">上一页</a>`;
                        pagination.appendChild(prevLi);
            
                        // 页码按钮
                        console.log(currentPage);
                        if(totalPages >= 10){
                            if(currentPage + 10 < totalPages) {
                                for (let i = currentPage; i <= currentPage+10; i++) {
                                    console.log(i);
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                            else{
                                for(let i = totalPages - 10; i<=totalPages;i++){
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch}, ${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                        }
                        else{
                            for (let i = 1; i <= totalPages; i++) {
                                const pageLi = document.createElement('li');
                                pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                pagination.appendChild(pageLi);
                            }
                        }
            
                        // 下一页按钮
                        const nextLi = document.createElement('li');
                        nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
                        nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${page + 1})">下一页</a>`;
                        pagination.appendChild(nextLi);
                    });
                }
                else if(type === 'backbone'){
                    fetch(`/LabDatabase/getdata?type=backbone&page=${page}`)
                    .then(response => response.json())
                    .then(data =>{
                        console.log(data);
                        result = data.data;
                        totalItems = data.pagination.total_count;
                        totalPages = data.pagination.total_pages;
                        currentPage = data.pagination.current_page;
                        offset = data.pagination.offset;
                        
                        tableBody.innerHTML = '';
                        if (totalItems === 0) {
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="7">
                                        <div class="empty-state">
                                            <div class="empty-icon">📭</div>
                                            <div>没有找到数据</div>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        } else {
                            result.forEach(item => {
                                const row = document.createElement('tr');
                                row.setAttribute("id", `backbone_row_${item.id}`)
                                row.innerHTML = `
                                    <td>${item.name}</td>
                                    <td>${item.alias}</td>
                                    <td>${item.marker.join(", ")}</td>
                                    <td>${item.ori.join(", ")}</td>
                                    <td>${item.species}</td>
                                    <td>${item.scar}</td>
                                    <td><span class="status-badge ${item.tag === 'normal' ? 'status-active' : 'status-inactive'}">${item.tag === 'normal' ? '正常' : '非正常'}</span></td>
                                    <td class="action-cell">
                                        <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/LabDatabase/backbone/${item.id}'">查看</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="window.location.href='/LabDatabase/modifybackbone/${item.id}'">编辑</button>
                                        <button class="btn btn-sm btn-outline-danger" onclick="DeleteBackbone(${item.id})">删除</button>
                                    </td>
                                `;
                                tableBody.appendChild(row);
                            })
                        }
                        // 更新分页信息
                        paginationInfo.textContent = `显示 ${totalItems} 条记录中的 ${offset} 到 ${offset+10} 条`;
            
                        // 生成分页控件
                        pagination.innerHTML = '';
            
                        // 上一页按钮
                        const prevLi = document.createElement('li');
                        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
                        prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page - 1})">上一页</a>`;
                        pagination.appendChild(prevLi);
            
                        // 页码按钮
                        if(totalPages >= 10){
                            if(currentPage + 10 < totalPages) {
                                for (let i = currentPage; i <= currentPage+10; i++) {
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                            else{
                                for(let i = totalPages - 10; i<=totalPages;i++){
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                        
                        }
                        else{
                            for (let i = 1; i <= totalPages; i++) {
                                const pageLi = document.createElement('li');
                                pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                pagination.appendChild(pageLi);
                            }
                        }
            
                        // 下一页按钮
                        const nextLi = document.createElement('li');
                        nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
                        nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page + 1})">下一页</a>`;
                        pagination.appendChild(nextLi);
                    });
                }
                else if(type === 'plasmid'){
                    fetch(`/LabDatabase/getdata?type=plasmid&page=${page}`)
                    .then(response => response.json())
                    .then(data => {
                        console.log(data);
                        result = data.data;
                        totalItems = data.pagination.total_count;
                        totalPages = data.pagination.total_pages;
                        currentPage = data.pagination.current_page;
                        offset = data.pagination.offset;

                        tableBody.innerHTML = '';
                        if (totalItems === 0) {
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="7">
                                        <div class="empty-state">
                                            <div class="empty-icon">📭</div>
                                            <div>没有找到数据</div>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        } else {
                            result.forEach(item => {
                                const row = document.createElement('tr');
                                row.setAttribute("id", `plasmid_row_${item.plasmidid}`)
                                const oriList = ensureArray(item.ori_info);
                                const markerList = ensureArray(item.marker_info);
                                row.innerHTML = `
                                    <td>${item.name}</td>
                                    <td>${item.alias}</td>
                                    <td>${oriList.join(", ") || "-"}</td>
                                    <td>${markerList.join(", ") || "-"}</td>
                                    <td>${item.level}</td>
                                    <td>${renderRelatedSummary(item)}</td>
                                    <td>${item.scar || "-"}</td>
                                    <td><span class="status-badge ${item.tag === 'normal' ? 'status-active' : 'status-inactive'}">${item.tag === 'normal' ? '正常' : '非正常'}</span></td>
                                    <td class="action-cell">
                                        <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/LabDatabase/plasmid/${item.plasmidid}'">查看</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="window.location.href='/LabDatabase/modifyplasmid/${item.plasmidid}'">编辑</button>
                                        <button class="btn btn-sm btn-outline-danger" onclick = "PlasmidDelete(${item.plasmidid})">删除</button>
                                    </td>
                                `;
                                tableBody.appendChild(row);
                            })
                        }
                        // 更新分页信息
                        paginationInfo.textContent = `显示 ${totalItems} 条记录中的 ${offset} 到 ${offset+10} 条`;
            
                        // 生成分页控件
                        pagination.innerHTML = '';
            
                        // 上一页按钮
                        const prevLi = document.createElement('li');
                        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
                        prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page - 1})">上一页</a>`;
                        pagination.appendChild(prevLi);
            
                        // 页码按钮
                        if(totalPages >= 10){
                            if(currentPage + 10 < totalPages) {
                                for (let i = currentPage; i <= currentPage+10; i++) {
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                            else{
                                for(let i = totalPages - 10; i<=totalPages;i++){
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                        
                        }
                        else{
                            for (let i = 1; i <= totalPages; i++) {
                                const pageLi = document.createElement('li');
                                pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${i})">${i}</a>`;
                                pagination.appendChild(pageLi);
                            }
                        }
                    
            
                        // 下一页按钮
                        const nextLi = document.createElement('li');
                        nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
                        nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page + 1})">下一页</a>`;
                        pagination.appendChild(nextLi);
                    });
                }
            }

            //搜索渲染
            else{
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                if(type === 'part'){
                    const request_body = {'SearchType':"part",'name':document.getElementById('PartSearchInput').value,
                    'Type':document.getElementById('PartTypeSelect').options[document.getElementById('PartTypeSelect').selectedIndex].text,
                    'Enzyme':document.getElementById('PartEnzyme').options[document.getElementById('PartEnzyme').selectedIndex].text,
                    'Scar':document.getElementById('PartScar').options[document.getElementById('PartScar').selectedIndex].text,
                    'page' : page, 'page_size':10}
                    fetch(`/LabDatabase/filterdata`,{
                        method:'POST',
                        body: JSON.stringify(request_body),
                        headers:{
                            'X-CSRFToken':csrfToken,
                            'Content-Type':"application/json",
                        },
                    })
                    .then(response => response.json())
                    .then(data =>{
                        if(data.success){
                            result = data.data;
                            totalItems = data.pagination.total_count;
                            totalPages = data.pagination.total_pages;
                            currentPage = data.pagination.current_page;
                            offset = data.pagination.offset;
                            
                            tableBody.innerHTML = '';
                            if (totalItems === 0) {
                                tableBody.innerHTML = `
                                <tr>
                                    <td colspan="7">
                                        <div class="empty-state">
                                            <div class="empty-icon">📭</div>
                                            <div>没有找到数据</div>
                                        </div>
                                    </td>
                                </tr>
                                `;
                            } else {
                            // 填充表格数据
                                result.forEach(item => {
                                    const row = document.createElement('tr');
                                    row.setAttribute("id", `part_row_${item.partid}`)
                                    let PartType = "";
                                    if(item.type === 1){
                                        PartType = "promoter";
                                    }
                                    else if(item.type === 2){
                                        PartType = "CDS";
                                    }
                                    else if(item.type === 3){
                                        PartType = "Terminator";
                                    }
                                    else if(item.type === 4){
                                        PartType = "RBS";
                                    }
                                    else if(item.type === 5){
                                        PartType = "P+R";
                                    }
                                    row.innerHTML = `
                                        <td>${item.name}</td>
                                        <td>${item.alias}</td>
                                        <td>${PartType}</td>
                                        <td>${item.sourceorganism}</td>
                                        <td>${item.reference}</td>
                                        <td><span class="status-badge ${item.tag === 'normal' ? 'status-active' : 'status-inactive'}">${item.tag === 'normal' ? '正常' : '非正常'}</span></td>
                                        <td class="action-cell">
                                            <button class="btn btn-sm btn-outline-primary"  onclick="window.location.href='/LabDatabase/part/${item.partid}'">查看</button>
                                            <button class="btn btn-sm btn-outline-secondary" onclick="window.location.href='/LabDatabase/modifypart/${item.partid}'">编辑</button>
                                            <button class="btn btn-sm btn-outline-danger" onclick = "DeletePart(${item.partid})">删除</button>
                                        </td>
                                        `;
                                    tableBody.appendChild(row);
                                })
                            }
                            // 更新分页信息
                            paginationInfo.textContent = `显示 ${totalItems} 条记录中的 ${offset} 到 ${offset+10} 条`;
            
                            // 生成分页控件
                            pagination.innerHTML = '';
            
                            // 上一页按钮
                            const prevLi = document.createElement('li');
                            prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
                            prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch}, ${page - 1})">上一页</a>`;
                            pagination.appendChild(prevLi);
            
                            // 页码按钮
                            console.log(currentPage);
                            if(totalPages >= 10){
                                if(currentPage + 10 < totalPages) {
                                    for (let i = currentPage; i <= currentPage+10; i++) {
                                        console.log(i);
                                        const pageLi = document.createElement('li');
                                        pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                        pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                        pagination.appendChild(pageLi);
                                    }
                                }
                                else{
                                    for(let i = totalPages - 10; i<=totalPages;i++){
                                        const pageLi = document.createElement('li');
                                        pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                        pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch}, ${i})">${i}</a>`;
                                        pagination.appendChild(pageLi);
                                    }
                                }
                            }
                            else{
                                for (let i = 1; i <= totalPages; i++) {
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
            
                            // 下一页按钮
                            const nextLi = document.createElement('li');
                            nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
                            nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${page + 1})">下一页</a>`;
                            pagination.appendChild(nextLi);
                        }
                        else{
                            tableBody.innerHTML = '';
                            tableBody.innerHTML = `
                            <tr>
                                <td colspan="7">
                                    <div class="empty-state">
                                        <div class="empty-icon">📭</div>
                                        <div>没有找到数据</div>
                                    </div>
                                </td>
                            </tr>
                        `;
                        }
                    });
                }
                else if(type === 'backbone'){
                    // let fd = new FormData();
                    // fd.append('SearchType','backbone');
                    // fd.append('name',document.getElementById('BackboneSearchInput').innerText);
                    // fd.append('Ori',document.getElementById('OriSelect').innerText);
                    // fd.append('Marker',document.getElementById('MarkerSelect').innerText);
                    // fd.append('Enzyme',document.getElementById('BackboneEnzyme').innerText);
                    // fd.append('Scar',document.getElementById('BackboneScar').innerText);
                    // fd.append('page',page);
                    // fd.append('page_size',10);
                    const request_body = {"SearchType":'backbone',"name":document.getElementById('BackboneSearchInput').value,
                    "Ori":document.getElementById("OriSelect").options[document.getElementById("OriSelect").selectedIndex].text,
                    "Marker":document.getElementById("MarkerSelect").options[document.getElementById("MarkerSelect").selectedIndex].text,
                    "Enzyme":document.getElementById("BackboneEnzyme").options[document.getElementById("BackboneEnzyme").selectedIndex].text,
                    "Scar":document.getElementById("BackboneScar").options[document.getElementById("BackboneScar").selectedIndex].text,
                    "page":page, "page_size":10}

                    fetch(`/LabDatabase/filterdata`,{
                        method:'POST',
                        body: JSON.stringify(request_body),
                        headers:{
                            'X-CSRFToken':csrfToken,
                            'Content-Type':"application/json",
                        }
                    })
                    .then(response => response.json())
                    .then(data =>{
                        if(data.success){

                        console.log(data);
                        result = data.data;
                        totalItems = data.pagination.total_count;
                        totalPages = data.pagination.total_pages;
                        currentPage = data.pagination.current_page;
                        offset = data.pagination.offset;
                        // scar = document.getElementById('BackboneScar').options[document.getElementById('BackboneScar').selectedIndex].text
                        tableBody.innerHTML = '';
                        if (totalItems === 0) {
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="7">
                                        <div class="empty-state">
                                            <div class="empty-icon">📭</div>
                                            <div>没有找到数据</div>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        } else {
                            result.forEach(item => {
                                const row = document.createElement('tr');
                                row.setAttribute("id", `backbone_row_${item.id}`)
                                row.innerHTML = `
                                    <td>${item.name}</td>
                                    <td>${item.alias}</td>
                                    <td>${item.marker.join(", ")}</td>
                                    <td>${item.ori.join(", ")}</td>
                                    <td>${item.species}</td>
                                    <td>${item.scar}</td>
                                    <td><span class="status-badge ${item.tag === 'normal' ? 'status-active' : 'status-inactive'}">${item.tag === 'normal' ? '正常' : '非正常'}</span></td>
                                    <td class="action-cell">
                                        <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/LabDatabase/backbone/${item.id}'">查看</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="window.location.href='/LabDatabase/modifybackbone/${item.id}'">编辑</button>
                                        <button class="btn btn-sm btn-outline-danger" onclick = "DeleteBackbone(${item.id})">删除</button>
                                    </td>
                                `;
                                tableBody.appendChild(row);
                            })
                        }
                        // 更新分页信息
                        paginationInfo.textContent = `显示 ${totalItems} 条记录中的 ${offset} 到 ${offset+10} 条`;
            
                        // 生成分页控件
                        pagination.innerHTML = '';
            
                        // 上一页按钮
                        const prevLi = document.createElement('li');
                        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
                        prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page - 1})">上一页</a>`;
                        pagination.appendChild(prevLi);
            
                        // 页码按钮
                        if(totalPages >= 10){
                            if(currentPage + 10 < totalPages) {
                                for (let i = currentPage; i <= currentPage+10; i++) {
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                            else{
                                for(let i = totalPages - 10; i<=totalPages;i++){
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                        
                        }
                        else{
                            for (let i = 1; i <= totalPages; i++) {
                                const pageLi = document.createElement('li');
                                pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                pagination.appendChild(pageLi);
                            }
                        }
            
                        // 下一页按钮
                        const nextLi = document.createElement('li');
                        nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
                        nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page + 1})">下一页</a>`;
                        pagination.appendChild(nextLi);
                        }
                        else{
                            tableBody.innerHTML = '';
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="7">
                                        <div class="empty-state">
                                            <div class="empty-icon">📭</div>
                                            <div>没有找到数据</div>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }
                    });
                }
                else if(type === 'plasmid'){
                    // const fd = new FormData();
                    // fd.append('SearchType','plasmid');
                    // fd.append('name',docuemnt.getElementById('PlasmidSearchInput').innerText);
                    // fd.append('OriClone',document.getElementById('OriCloneSelect').innerText);
                    // fd.append('MarkerClone',document.getElementById('MarkerCloneSelect').innerText);
                    // fd.append('OriHost',document.getElementById('OriHostSelect').innerText);
                    // fd.append('MarkerHost',document.getElementById('MarkerHostSelect').innerText);
                    // fd.append('Enzyme',document.getElementById('PlasmidEnzyme').innerText);
                    // fd.append('Scar',document.getElementById('PlasmidScar').innerText);
                    // fd.append('page',page);
                    // fd.append('page_size',10);
                    const request_body = {"SearchType":"plasmid", 'name':document.getElementById("PlasmidSearchInput").value,
                                    "Ori" : document.getElementById("OriSelectPlasmid").options[document.getElementById("OriSelectPlasmid").selectedIndex].text,
                                    "Marker" : document.getElementById("MarkerSelectPlasmid").options[document.getElementById("MarkerSelectPlasmid").selectedIndex].text,
                                    "Enzyme" : document.getElementById('PlasmidEnzyme').options[document.getElementById('PlasmidEnzyme').selectedIndex].text,
                                    "Scar" : document.getElementById('PlasmidScar').options[document.getElementById('PlasmidScar').selectedIndex].text,
                                    "page" : page, "page_size" : 10}
                    fetch(`/LabDatabase/filterdata`,{
                        method:'POST',
                        body: JSON.stringify(request_body),
                        headers:{
                            'X-CSRFToken':csrfToken,
                            'Content-Type':"application/json",
                        }
                    })
                    .then(response => response.json())
                    .then(data =>{
                        console.log(data);
                        result = data.data;
                        totalItems = data.pagination.total_count;
                        totalPages = data.pagination.total_pages;
                        currentPage = data.pagination.current_page;
                        offset = data.pagination.offset;
                        // scar = data.scar;
                        // scar = document.getElementById('PlasmidScar').options[document.getElementById('PlasmidScar').selectedIndex].text;
                        tableBody.innerHTML = '';
                        if (totalItems === 0) {
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="7">
                                        <div class="empty-state">
                                            <div class="empty-icon">📭</div>
                                            <div>没有找到数据</div>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        } else {
                            result.forEach(item => {
                                const row = document.createElement('tr');
                                row.setAttribute("id", `plasmid_row_${item.plasmidid}`)
                                row.innerHTML = `
                                    <td>${item.name}</td>
                                    <td>${item.alias}</td>
                                    <td>${ensureArray(item.ori_info).join(", ") || "-"}</td>
                                    <td>${ensureArray(item.marker_info).join(", ") || "-"}</td>
                                    <td>${item.level}</td>
                                    <td>${renderRelatedSummary(item)}</td>
                                    <td>${item.scar || "-"}</td>
                                    <td><span class="status-badge ${item.tag === 'normal' ? 'status-active' : 'status-inactive'}">${item.tag === 'normal' ? '正常' : '非正常'}</span></td>
                                    <td class="action-cell">
                                        <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/LabDatabase/plasmid/${item.plasmidid}'">查看</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="window.location.href='/LabDatabase/modifyplasmid/${item.plasmidid}'">编辑</button>
                                        <button class="btn btn-sm btn-outline-danger" onclick = "DeletePlasmid(${item.plasmidid})">删除</button>
                                    </td>
                                `;
                                tableBody.appendChild(row);
                            })
                        }
                        // 更新分页信息
                        paginationInfo.textContent = `显示 ${totalItems} 条记录中的 ${offset} 到 ${offset+10} 条`;
            
                        // 生成分页控件
                        pagination.innerHTML = '';
            
                        // 上一页按钮
                        const prevLi = document.createElement('li');
                        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
                        prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page - 1})">上一页</a>`;
                        pagination.appendChild(prevLi);
            
                        // 页码按钮
                        if(totalPages >= 10){
                            if(currentPage + 10 < totalPages) {
                                for (let i = currentPage; i <= currentPage+10; i++) {
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}', ${isSearch},${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                            else{
                                for(let i = totalPages - 10; i<=totalPages;i++){
                                    const pageLi = document.createElement('li');
                                    pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                    pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${i})">${i}</a>`;
                                    pagination.appendChild(pageLi);
                                }
                            }
                        
                        }
                        else{
                            for (let i = 1; i <= totalPages; i++) {
                                const pageLi = document.createElement('li');
                                pageLi.className = `page-item ${i === page ? 'active' : ''}`;
                                pageLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${i})">${i}</a>`;
                                pagination.appendChild(pageLi);
                            }
                        }
                    
            
                        // 下一页按钮
                        const nextLi = document.createElement('li');
                        nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
                        nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage('${type}',${isSearch} ,${page + 1})">下一页</a>`;
                        pagination.appendChild(nextLi);
                    });
                }
            }
            
        }

        // 切换页面
        function changePage(type,isSearch,newPage) {
            currentPage = newPage;
            renderTable(type, isSearch,newPage);
        }

        function renderselect(){
            const PartScar = document.getElementById('PartScar');
            const OriSelect = document.getElementById('OriSelect');
            const MarkerSelect = document.getElementById('MarkerSelect');
            const BackboneScar = document.getElementById('BackboneScar');
            const OriSelectPlasmid = document.getElementById('OriSelectPlasmid');
            const MarkerSelectPlasmid = document.getElementById('MarkerSelectPlasmid');
            const PlasmidScar = document.getElementById('PlasmidScar');
            //PartScarSelect
            fetch('/WebDatabase/getPartScarList')
            .then(response => response.json())
            .then(data =>{
                if(data.success){
                    let partscar = data.data;
                    partscar.forEach(item =>{
                        const scaroption = document.createElement('option');
                        scaroption.innerText = item;
                        PartScar.appendChild(scaroption);
                    });
                }
            });
            //Backbone Ori Select
            fetch('/WebDatabase/getBackboneValueList/ori')
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    let orilist = data.data;
                    console.log(orilist);
                    orilist.forEach(item => {
                        const orioption = document.createElement('option');
                        orioption.innerText = item;
                        OriSelect.appendChild(orioption);
                    })
                }
            });
            //Backbone Marker Select
            fetch('/WebDatabase/getBackboneValueList/marker')
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    let markerlist = data.data;

                    markerlist.forEach(item => {
                        const markeroption = document.createElement('option');
                        markeroption.innerText = item;
                        MarkerSelect.appendChild(markeroption);
                    })
                }
            });
            //Backbone Scar Select
            fetch('/WebDatabase/getBackboneScarList')
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    let Backbonescar = data.data;
                    Backbonescar.forEach(item =>{
                        const scaroption = document.createElement('option');
                        scaroption.innerText = item;
                        BackboneScar.appendChild(scaroption);
                    });
                }
            });

            //Plasmid Ori Clone Select
            fetch('/WebDatabase/getPlasmidValueList/ori')
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    let PlasmidOri = data.data;
                    PlasmidOri.forEach(item =>{
                        const orioption = document.createElement('option');
                        orioption.innerText = item;
                        OriSelectPlasmid.appendChild(orioption);
                    });
                }
            });

            //Plasmid Marker Clone Select
            fetch('/WebDatabase/getPlasmidValueList/marker')
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    let PlasmidMarker = data.data;
                    PlasmidMarker.forEach(item =>{
                        const Markeroption = document.createElement('option');
                        Markeroption.innerText = item;
                        MarkerSelectPlasmid.appendChild(Markeroption);
                    });
                }
            });


            //Plasmid Scar Select
            fetch('/WebDatabase/getPlasmidScarList')
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    let Plasmidscarlist = data.data;
                    Plasmidscarlist.forEach(item =>{
                        const PlasmidScarOption = document.createElement('option');
                        PlasmidScarOption.innerText = item;
                        PlasmidScar.appendChild(PlasmidScarOption);
                    });
                }
            });
        }

        function DeletePart(partid){
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            var confirmDelete = confirm("确定要删除吗？");
            if( !confirmDelete){
                event.preventDefault();
            }
            else{
                let request_body = {"partid":partid}

                fetch(`/LabDatabase/deletepart`,{
                    method:'POST',
                    body:JSON.stringify(request_body),
                    headers:{
                        'X-CSRFToken':csrfToken,
                        'Content-Type':"application/json",
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if(data.success){
                        alert("删除成功");
                        document.getElementById(`part_row_${partid}`).remove();

                    }
                    else{
                        alert(data.message);
                    }
                });
            }
            
        }

        function DeleteBackbone(Backboneid){
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            var confirmDelete = confirm("确定要删除吗？");
            if( !confirmDelete){
                event.preventDefault();
            }
            else{
                let request_body = {"backboneid":Backboneid}
                fetch(`/LabDatabase/deletebackbone`,{
                    method:'POST',
                    body:JSON.stringify(request_body),
                    headers:{
                        'X-CSRFToken':csrfToken,
                        'Content-Type':"application/json",
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if(data.success){
                        alert("删除成功");
                        document.getElementById(`backbone_row_${Backboneid}`).remove();

                    }
                    else{
                        alert(data.message);
                    }
                });
            }
        }
        
        function DeletePlasmid(Plasmidid){
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            var confirmDelete = confirm("确定要删除吗？");
            if( !confirmDelete){
                event.preventDefault();
            }
            else{
                let request_body = {"Plasmidid":Plasmidid, "CurrentPath":window.location.href}
                fetch(`/LabDatabase/deleteplasmid`,{
                    method:'POST',
                    body:JSON.stringify(request_body),
                    headers:{
                        'X-CSRFToken':csrfToken,
                        'Content-Type':"application/json",
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if(data.success){
                        alert("删除成功");
                        document.getElementById(`plasmid_row_${Plasmidid}`).remove();
                    }
                    else{
                        alert(data.message);
                    }
                });
            }
        }


        
        // // 关闭弹窗
        // function closeModalPlate() {
        //     const createPlateModal = bootstrap.Modal.getInstance(document.getElementById("modalOverlay-Plate"))
        //     createPlateModal.hide();
        // }
