
        // 当前选中的内容
        let currentContent = "dashboard";
        let currentWarehouseId = null;

        // DOM元素
        const warehouseNav = document.getElementById('warehouse-nav');
        const warehouseList = document.getElementById('warehouse-list');
        const navItems = document.querySelectorAll('.nav-item');
        const contentSections = document.querySelectorAll('.content-section');
        const warehouseContainer = document.getElementById('warehouse-container');
        const warehouseCountEl = document.getElementById('warehouse-count');
        const projectCountEl = document.getElementById('project-count');
        const componentCountEl = document.getElementById('component-count');
        const plasmidCountEl = document.getElementById('plasmid-count');

        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化仓库列表
            renderWarehouseList();
            
            setupMenuEvents();
            
            // // 更新统计信息
            // updateStats();
            
            // // 设置导航事件
            // setupNavigation();
            
            // 设置仓库导航展开/折叠
            // setupWarehouseNav();
            
            // 设置按钮事件
            setupButtons();

        });

        function setupMenuEvents(){
            const menuHeaders = document.querySelectorAll(".nav-item");
            menuHeaders.forEach(headers => {
                headers.addEventListener('click',function(e){
                    console.log("111111111111111111");
                    menuHeaders.forEach(i => i.classList.remove('active'));
                    headers.classList.add('active');
                    const tool = headers.getAttribute('data-content');
                    console.log(tool);
                    if(tool){
                        switchTool(tool);
                    }
                    e.stopPropagation();
                })
            });
        }

        function switchTool(tool){
            switch(tool){
                case "dashboard":
                    showdashbord();
                    break;
                case "profile":
                    showprofile();
                    break;
                case "warehouse":
                    showwarehouse();
                    break;
                case "projects":
                    showprojects();
                    break;
                case "templates":
                    showtemplates();
                    break;
                case "tools":
                    showtools();
                    break;
                case "settings":
                    showsettings();
                    break;
            }
        }

        function showdashbord(){
            document.getElementById("dashboard-content").style.display = "block";
            document.getElementById("profile-content").style.display = "none";
            document.getElementById("warehouse-content").style.display = "none";
            document.getElementById("projects-content").style.display = "none";
            document.getElementById("templates-content").style.display = "none";
            document.getElementById("tools-content").style.display = "none";
            document.getElementById("settings-content").style.display = "none";
        }

        function showprofile(){
            document.getElementById("dashboard-content").style.display = "none";
            document.getElementById("profile-content").style.display = "block";
            document.getElementById("warehouse-content").style.display = "none";
            document.getElementById("projects-content").style.display = "none";
            document.getElementById("templates-content").style.display = "none";
            document.getElementById("tools-content").style.display = "none";
            document.getElementById("settings-content").style.display = "none";
        }

        function showwarehouse(){
            document.getElementById("dashboard-content").style.display = "none";
            document.getElementById("profile-content").style.display = "none";
            document.getElementById("warehouse-content").style.display = "block";
            document.getElementById("projects-content").style.display = "none";
            document.getElementById("templates-content").style.display = "none";
            document.getElementById("tools-content").style.display = "none";
            document.getElementById("settings-content").style.display = "none";
        }

        function showprojects(){
            document.getElementById("dashboard-content").style.display = "none";
            document.getElementById("profile-content").style.display = "none";
            document.getElementById("warehouse-content").style.display = "none";
            document.getElementById("projects-content").style.display = "block";
            document.getElementById("templates-content").style.display = "none";
            document.getElementById("tools-content").style.display = "none";
            document.getElementById("settings-content").style.display = "none";
        }

        function showtemplates(){
            document.getElementById("dashboard-content").style.display = "none";
            document.getElementById("profile-content").style.display = "none";
            document.getElementById("warehouse-content").style.display = "none";
            document.getElementById("projects-content").style.display = "none";
            document.getElementById("templates-content").style.display = "block";
            document.getElementById("tools-content").style.display = "none";
            document.getElementById("settings-content").style.display = "none";
        }

        function showtools(){
            document.getElementById("dashboard-content").style.display = "none";
            document.getElementById("profile-content").style.display = "none";
            document.getElementById("warehouse-content").style.display = "none";
            document.getElementById("projects-content").style.display = "none";
            document.getElementById("templates-content").style.display = "none";
            document.getElementById("tools-content").style.display = "block";
            document.getElementById("settings-content").style.display = "none";
        }

        function showsettings(){
            document.getElementById("dashboard-content").style.display = "none";
            document.getElementById("profile-content").style.display = "none";
            document.getElementById("warehouse-content").style.display = "none";
            document.getElementById("projects-content").style.display = "none";
            document.getElementById("templates-content").style.display = "none";
            document.getElementById("tools-content").style.display = "none";
            document.getElementById("settings-content").style.display = "block";
        }

        // 渲染侧边栏仓库列表
        function renderWarehouseList() {
            fetch('/WebDatabase/getrepos')
            .then(response => response.json())
            .then(data =>{
                if(data.success){
                    warehouseList.innerHTML = '';
                    data.repo.forEach(warehouse => {
                        console.log("renderWarehouseList");
                        const warehouseItem = document.createElement('div');
                        warehouseItem.className = 'warehouse-subitem';
                        // warehouseItem.dataset.name = warehouse.name;
                        // warehouseItem.dataset.content = 'warehouse-detail';
                
                        warehouseItem.innerHTML = `
                            <i class="fas fa-warehouse"></i>
                            <span>${warehouse.name}</span>
                        `;
                        console.log(warehouseItem.innerHTML)
                        warehouseItem.addEventListener('click', function(e) {
                            e.stopPropagation();
                            // 更新选中状态
                            updateNavSelection(this, 'warehouse-subitem');
                            // 显示仓库详情
                            showWarehouseDetail(warehouse.name);
                            // 切换到仓库内容
                            showwarehouse();
                            // 滚动到仓库详情
                            currentWarehouseId = warehouse.id;
                        });
                        warehouseList.appendChild(warehouseItem);
                    })
                    warehouseContainer.innerHTML = '';

                    if (data.repo.length == 0){
                        warehouseContainer.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-warehouse"></i>
                                <h3>暂无组装仓库</h3>
                                <p>点击"新建仓库"按钮创建您的第一个基因组装仓库</p>
                            </div>
                        `;
                        return;
                    }
                    data.repo.forEach(warehouse => {
                        console.log(warehouse);
                        const warehouseCard = document.createElement('div');
                        warehouseCard.className = 'warehouse-card fade-in';
                        // warehouseCard.dataset.name = warehouse.name;

                        warehouseCard.innerHTML = `
                            <div class="warehouse-card-header">
                                <div class="warehouse-name">${warehouse.name}</div>
                                <div class="warehouse-id">${warehouse.id}</div>
                            </div>
                            <p style="color: #64748b; margin-bottom: 15px;">${warehouse.note}</p>
                            <div class="warehouse-stats">
                                <div class="warehouse-stat">
                                    <i class="fas fa-dna"></i>
                                    <span>${warehouse.data.parts.length} 个元件</span>
                                </div>
                                <div class="warehouse-stat">
                                    <i class="fas fa-vector-square"></i>
                                    <span>${warehouse.data.backbones.length} 个载体</span>
                                </div>
                                <div class="warehouse-stat">
                                    <i class="fas fa-circle-dna"></i>
                                    <span>${warehouse.data.plasmids.length} 个质粒</span>
                                </div>
                            </div>
                            <div class="warehouse-tags">
                            </div>
                        `;
                        
                        warehouseCard.addEventListener('click', function() {
                            const warehouseName = this.querySelector('.warehouse-name').textContent;
                    
                            // 更新侧边栏选中状态
                            updateNavSelectionForWarehouse(warehouseName);
                    
                            // 显示仓库详情
                            showWarehouseDetail(warehouseName);
                    
                            // 确保仓库列表是展开的
                            if (!warehouseList.classList.contains('expanded')) {
                                warehouseList.classList.add('expanded');
                                warehouseNav.querySelector('.nav-arrow').classList.add('rotated');
                            }
                        });
                        warehouseContainer.appendChild(warehouseCard);
                    });


                    warehouseNav.addEventListener('click', function(e) {
                        e.stopPropagation();
                        // 切换展开/折叠状态
                        warehouseList.classList.toggle('expanded');
                        this.querySelector('.nav-arrow').classList.toggle('rotated');
                        
                        // 如果展开并且没有选中仓库子项，选中第一个
                        if (warehouseList.classList.contains('expanded')) {
                            // 切换到仓库内容
                            showwarehouse();
                    
                            // 更新导航选中状态
                            updateNavSelection(this, 'nav-item');
                    
                            // // 如果没有选中的仓库子项，选中第一个
                            // if (!currentWarehouseId) {
                            //     setTimeout(() => {
                            //         const firstWarehouse = document.querySelector('.warehouse-subitem');
                            //         if (firstWarehouse) {
                            //             updateNavSelection(firstWarehouse, 'warehouse-subitem');
                            //             console.log(data.repo[0].name);
                            //             showWarehouseDetail(data.repo[0].name);
                            //         }
                            //     }, 100);
                            // }
                        }
                    });


                    
                }
            });
        }


        // 显示仓库详情
        function showWarehouseDetail(warehouseName) {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            window.location.href = `/LabDatabase/ShowRepository/${warehouseName}`;
            // fetch(`/WebDatabase/ShowRepository/${warehouseName}`,{
            //     method: "GET",
            //     headers:{
            //         'X-CSRFToken': csrfToken,
            //     },
            // }).then(response => response.json())
            // .then(data =>{
            //     if(data.success){
            //         // document.querySelector('#warehouse-content .content-header h2').textContent = warehouseName;
            //         // document.querySelector('#warehouse-content .content-subtitle').textContent = data.repository;
            //         fetch(`/LabDatabase/ShowRepository/${warehouseName}`
            //     }
            //     else{
            //         return;
            //     }
            // })
        }


        // // 设置导航事件
        // function setupNavigation() {
        //     navItems.forEach(item => {
        //         // 排除仓库导航（它有特殊的展开/折叠功能）
        //         if (item.id !== 'warehouse-nav') {
        //             item.addEventListener('click', function() {
        //                 const content = this.dataset.content;
                        
        //                 // 更新导航选中状态
        //                 updateNavSelection(this, 'nav-item');
                        
        //                 // 切换到对应内容
        //                 switchContent(content);
                        
        //                 // 如果点击的是其他导航项，折叠仓库列表
        //                 if (content !== 'warehouse') {
        //                     warehouseList.classList.remove('expanded');
        //                     warehouseNav.querySelector('.nav-arrow').classList.remove('rotated');
        //                 }
        //             });
        //         }
        //     });
            
        //     // 点击用户资料头
        //     document.getElementById('profile-header').addEventListener('click', function() {
        //         updateNavSelection(document.querySelector('.nav-item[data-content="profile"]'), 'nav-item');
        //         switchContent('profile');
        //     });
        // }

        // // 设置仓库导航展开/折叠
        // function setupWarehouseNav() {
        //     warehouseNav.addEventListener('click', function(e) {
        //         e.stopPropagation();
        //         console.log("aaa");
                
        //         // 切换展开/折叠状态
        //         warehouseList.classList.toggle('expanded');
        //         console.log("pppppppp");
        //         this.querySelector('.nav-arrow').classList.toggle('rotated');
                
        //         // 如果展开并且没有选中仓库子项，选中第一个
        //         if (warehouseList.classList.contains('expanded')) {
        //             // 切换到仓库内容
        //             showwarehouse();
                    
        //             // 更新导航选中状态
        //             updateNavSelection(this, 'nav-item');
                    
        //             // // 如果没有选中的仓库子项，选中第一个
        //             // if (!currentWarehouseId) {
        //             //     setTimeout(() => {
        //             //         const firstWarehouse = document.querySelector('.warehouse-subitem');
        //             //         if (firstWarehouse) {
        //             //             updateNavSelection(firstWarehouse, 'warehouse-subitem');
        //             //             showWarehouseDetail(warehouses[0].id);
        //             //         }
        //             //     }, 100);
        //             // }
        //         }
        //     });
        // }

        // 更新导航选中状态
        function updateNavSelection(selectedElement, className) {
            // 移除所有同类的active类
            document.querySelectorAll(`.${className}`).forEach(item => {
                item.classList.remove('active');
            });
            
            // 为选中元素添加active类
            selectedElement.classList.add('active');
            
            // 如果是仓库子项，也高亮父级
            if (className === 'warehouse-subitem') {
                warehouseNav.classList.add('active');
            }
        }

        // 为仓库更新侧边栏选中状态
        function updateNavSelectionForWarehouse(warehouseId) {
            // 移除所有仓库子项的active类
            document.querySelectorAll('.warehouse-subitem').forEach(item => {
                item.classList.remove('active');
            });
            
            // 为对应仓库添加active类
            const warehouseItem = document.querySelector(`.warehouse-subitem[data-id="${warehouseId}"]`);
            if (warehouseItem) {
                warehouseItem.classList.add('active');
                warehouseNav.classList.add('active');
            }
        }

        // 切换内容区域
        function switchContent(content) {
            // 隐藏所有内容区域
            contentSections.forEach(section => {
                section.classList.remove('active');
            });
            
            // 显示选中的内容区域
            const targetSection = document.getElementById(`${content}-content`);
            if (targetSection) {
                targetSection.classList.add('active');
                currentContent = content;
            }
        }

        // 设置按钮事件
        function setupButtons() {
            // 新建仓库按钮
            document.getElementById('create-warehouse-btn').addEventListener('click', function() {
                
                
                // 重新渲染仓库列表
                renderWarehouseList();
                renderWarehouseContent();
                
                // // 更新统计信息
                // updateStats();
                
                // 展开仓库列表
                warehouseList.classList.add('expanded');
                warehouseNav.querySelector('.nav-arrow').classList.add('rotated');
                
                // 切换到仓库内容
                switchContent('warehouse');
                
                // 选中新仓库
                setTimeout(() => {
                    const newWarehouseItem = document.querySelector(`.warehouse-subitem`);
                    if (newWarehouseItem) {
                        updateNavSelection(newWarehouseItem, 'warehouse-subitem');
                        showWarehouseDetail(warehouse.name);
                    }
                }, 100);
                
                alert(`新仓库已创建！`);
            });
            
            // 退出登录按钮
            document.getElementById('logout-btn').addEventListener('click', function() {
                if (confirm('确定要退出登录吗？')) {
                    alert('已退出登录，正在跳转到登录页面...');
                    // 在实际应用中，这里会跳转到登录页面
                    // window.location.href = '/login';
                }
            });
        }