// 全局变量
        let currentUserPage = 1;
        let userPageSize = 20;
        let userSearchQuery = '';
        let userSortBy = '-total_components';
        let exportJobChecker = null;
        
        // DOM加载完成后执行
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化标签页
            const tabTriggerList = [].slice.call(document.querySelectorAll('a[data-bs-toggle="tab"]'));
            tabTriggerList.forEach(function(tabTriggerEl) {
                tabTriggerEl.addEventListener('shown.bs.tab', function(event) {
                    const targetId = event.target.getAttribute('href').substring(1);
                    handleTabChange(targetId);
                });
            });
            
            // 加载用户列表
            loadUserList();
            
            // 加载导出历史
            loadExportHistory();
            
            // // 初始化图表
            // initCharts();
            
            // 全选用户功能
            document.getElementById('selectAllUsers').addEventListener('change', function() {
                const userSelect = document.getElementById('userSelect');
                if (this.checked) {
                    for (let option of userSelect.options) {
                        option.selected = true;
                    }
                }
            });
        });
        
        // 标签页切换处理
        function handleTabChange(tabId) {
            switch(tabId) {
                case 'user-stats':
                    //用户统计
                    loadUserStats();
                    break;
                case 'export-history':
                    //导出历史
                    loadExportHistory();
                    break;
            }
        }
        
        // // 初始化图表
        // function initCharts() {
        //     // 上传趋势图
        //     const uploadCtx = document.getElementById('uploadChart').getContext('2d');
        //     const uploadData = {
        //         labels: {{ daily_stats|safe }},
        //         datasets: [{
        //             label: '上传数量',
        //             data: {{ daily_stats|safe }},
        //             borderColor: 'rgb(54, 162, 235)',
        //             backgroundColor: 'rgba(54, 162, 235, 0.1)',
        //             fill: true,
        //             tension: 0.4
        //         }]
        //     };
            
            // new Chart(uploadCtx, {
            //     type: 'line',
            //     data: uploadData,
            //     options: {
            //         responsive: true,
            //         maintainAspectRatio: false,
            //         plugins: {
            //             legend: {
            //                 display: false
            //             }
            //         }
            //     }
            // });
            
        //     // 类型分布图
        //     const typeCtx = document.getElementById('typeChart').getContext('2d');
        //     const typeData = {
        //         labels: {{ type_distribution|safe }},
        //         datasets: [{
        //             data: {{ type_distribution|safe }},
        //             backgroundColor: [
        //                 '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        //                 '#9966FF', '#FF9F40'
        //             ]
        //         }]
        //     };
            
        //     new Chart(typeCtx, {
        //         type: 'pie',
        //         data: typeData,
        //         options: {
        //             responsive: true,
        //             maintainAspectRatio: false,
        //             plugins: {
        //                 legend: {
        //                     position: 'right'
        //                 }
        //             }
        //         }
        //     });
        // }
        
        // 加载用户统计
        function loadUserStats() {
            showLoading('正在加载用户统计...');
            
            const search = document.getElementById('userSearch').value;
            const sortBy = document.getElementById('sortBy').value;
            
            const params = new URLSearchParams({
                search: search,
                sort_by: sortBy,
                page: currentUserPage,
                page_size: userPageSize
            });
            
            fetch(`/WebDatabase/getalluseruploadlist`)
                .then(response => response.json())
                .then(data => {
                    console.log(data.data);
                    updateUserStatsTable(data.data);
                    hideLoading();
                })
                .catch(error => {
                    console.error('加载用户统计失败:', error);
                    hideLoading();
                    showError('加载用户统计失败');
                });
        }
        
        // 更新用户统计表格
        function updateUserStatsTable(data) {
            const tbody = document.getElementById('userStatsBody');
            tbody.innerHTML = '';
            
            data.forEach(user => {
                // const lastUpload = user.last_upload_time
                //     ? formatDateTime(user.last_upload_time)
                //     : '从未上传';
                console.log(user);
                const row = `
                    <tr>
                        <td>
                            <div class="d-flex align-items-center">
                                <div class="user-avatar">
                                    ${user.uname ? user.uname.charAt(0) : user.uname.charAt(0)}
                                </div>
                                <div>
                                    <a href="/LabDatabase/user_detail/" 
                                       class="user-link" target="_blank">
                                        ${user.uname ? `${user.uname}` : user.uname}
                                    </a>
                                    
                                </div>
                            </div>
                        </td>
                        <td>
                            <span class="badge bg-primary">${user.part_count+user.backbone_count+user.plasmid_count}</span>
                        </td>
                        <td>
                            <span class="badge badge-approved">${user.part_count}</span>
                        </td>
                        <td>
                            <span class="badge badge-pending">${user.backbone_count}</span>
                        </td>
                        <td>
                            <span class="badge badge-rejected">${user.plasmid_count}</span>
                        </td>
                        
                        <td>
                            <button class="btn btn-sm btn-outline-primary"
                                    onclick="viewUserComponents('${user.uname}')">
                                查看元件
                            </button>
                            <button class="btn btn-sm btn-outline-info"
                                    onclick="exportUserData('${user.uname}')">
                                导出数据
                            </button>
                        </td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
            
            // 更新分页
            updateUserPagination(data.pagination);
        }
        
        // 更新用户分页
        function updateUserPagination(pagination) {
            // const paginationEl = document.getElementById('userPagination');
            // paginationEl.innerHTML = '';
            
            // // 上一页
            // if (pagination.has_previous) {
            //     paginationEl.innerHTML += `
            //         <li class="page-item">
            //             <a class="page-link" href="#" onclick="goToUserPage(${pagination.page - 1})">
            //                 上一页
            //             </a>
            //         </li>
            //     `;
            // }
            
            // // 页码
            // const startPage = Math.max(1, pagination.page - 2);
            // const endPage = Math.min(pagination.total_pages, pagination.page + 2);
            
            // for (let i = startPage; i <= endPage; i++) {
            //     paginationEl.innerHTML += `
            //         <li class="page-item ${i === pagination.page ? 'active' : ''}">
            //             <a class="page-link" href="#" onclick="goToUserPage(${i})">
            //                 ${i}
            //             </a>
            //         </li>
            //     `;
            // }
            
            // // 下一页
            // if (pagination.has_next) {
            //     paginationEl.innerHTML += `
            //         <li class="page-item">
            //             <a class="page-link" href="#" onclick="goToUserPage(${pagination.page + 1})">
            //                 下一页
            //             </a>
            //         </li>
            //     `;
            // }
        }
        
        // 跳转到用户页
        function goToUserPage(page) {
            currentUserPage = page;
            alert("跳转到用户页");
        }
        
        // 搜索用户
        function searchUsers() {
            currentUserPage = 1;
            loadUserStats();
        }
        
        // 查看用户元件
        function viewUserComponents(userId) {
            console.log(userId);
            // window.open(`/admin/user/${userId}/components/`, '_blank');
        }
        
        // 加载用户列表（用于导出筛选）
        function loadUserList() {
            fetch('/WebDatabase/getuserlist')
            .then(response => response.json())
            .then(data => {
                const userSelect = document.getElementById('userSelect');
                userSelect.innerHTML = '';
                console.log(data.data);
                data.data.forEach(user => {
                    const option = document.createElement('option');
                    option.text = `${user.uname}`;
                    userSelect.appendChild(option);
                });
            });
        }
        
        // 设置最近30天
        function setLast30Days() {
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 30);
            
            document.getElementById('startDate').value = thirtyDaysAgo.toISOString().split('T')[0];
            document.getElementById('endDate').value = today.toISOString().split('T')[0];
        }
        
        // 提交导出请求
        // function submitExport() {
        //     // 收集筛选条件
        //     const filters = {
        //         start_date: document.getElementById('startDate').value || null,
        //         end_date: document.getElementById('endDate').value || null,
        //         user_ids: Array.from(document.getElementById('userSelect').selectedOptions)
        //             .map(option => parseInt(option.value)),
        //         component_types: Array.from(document.querySelectorAll('.component-type:checked'))
        //             .map(checkbox => checkbox.value),
        //         statuses: Array.from(document.querySelectorAll('.component-status:checked'))
        //             .map(checkbox => checkbox.value),
        //         format: document.getElementById('exportFormat').value,
        //         include_sequence: document.getElementById('includeSequence').checked,
        //         include_attachments: document.getElementById('includeAttachments').checked
        //     };
            
        //     // 如果没有选择用户，清空数组
        //     if (filters.user_ids.length === 0) {
        //         delete filters.user_ids;
        //     }
            
        //     // 验证
        //     if (filters.start_date && filters.end_date) {
        //         const start = new Date(filters.start_date);
        //         const end = new Date(filters.end_date);
        //         if (start > end) {
        //             showError('开始日期不能晚于结束日期');
        //             return;
        //         }
        //     }
            
        //     showLoading('正在创建导出任务...');
            
        //     fetch('/LabDatabase/export/', {
        //         method: 'POST',
        //         headers: {
        //             'Content-Type': 'application/json',
        //             'X-CSRFToken': getCSRFToken()
        //         },
        //         body: JSON.stringify(filters)
        //     })
        //         .then(response => response.json())
        //         .then(data => {
        //             hideLoading();
                    
        //             if (data.job_id) {
        //                 Swal.fire({
        //                     title: '导出任务已创建',
        //                     text: '任务正在后台处理，处理完成后会自动通知您',
        //                     icon: 'success',
        //                     confirmButtonText: '确定'
        //                 }).then(() => {
        //                     // 切换到导出历史标签页
        //                     document.querySelector('a[href="#export-history"]').click();
        //                     // 开始检查任务状态
        //                     startCheckingJobStatus(data.job_id);
        //                 });
        //             }
        //         })
        //         .catch(error => {
        //             console.error('创建导出任务失败:', error);
        //             hideLoading();
        //             showError('创建导出任务失败');
        //         });
        // }
        
        // 开始检查任务状态
        function startCheckingJobStatus(jobId) {
            // 如果已有检查器，先清除
            if (exportJobChecker) {
                clearInterval(exportJobChecker);
            }
            
            exportJobChecker = setInterval(() => {
                checkJobStatus(jobId);
            }, 5000); // 每5秒检查一次
            
            // 首次检查
            checkJobStatus(jobId);
        }
        
        // 检查任务状态
        function checkJobStatus(jobId) {
            fetch(`/admin/api/export/`)
                .then(response => response.json())
                .then(jobs => {
                    const job = jobs.find(j => j.id === jobId);
                    
                    if (!job) return;
                    
                    // 找到对应的行并更新状态
                    const rows = document.querySelectorAll('#exportHistoryBody tr');
                    rows.forEach(row => {
                        if (row.dataset.jobId === jobId) {
                            updateJobRow(row, job);
                        }
                    });
                    
                    // 如果任务完成或失败，停止检查
                    if (job.status === 'completed' || job.status === 'failed') {
                        clearInterval(exportJobChecker);
                        exportJobChecker = null;
                        
                        if (job.status === 'completed') {
                            // 显示下载提示
                            Swal.fire({
                                title: '导出完成',
                                html: `文件已准备好，<a href="${job.download_url}" target="_blank">点击下载</a>`,
                                icon: 'success',
                                confirmButtonText: '确定'
                            });
                        }
                    }
                });
        }
        
        // 更新任务行
        function updateJobRow(row, job) {
            // 更新状态
            const statusCell = row.querySelector('.job-status');
            if (statusCell) {
                statusCell.innerHTML = getJobStatusBadge(job.status);
            }
            
            // 更新操作
            const actionCell = row.querySelector('.job-actions');
            if (actionCell) {
                actionCell.innerHTML = getJobActions(job);
            }
            
            // 更新文件大小
            const sizeCell = row.querySelector('.job-size');
            if (sizeCell && job.file_size) {
                sizeCell.textContent = formatFileSize(job.file_size);
            }
        }
        
        // 获取任务状态徽章
        function getJobStatusBadge(status) {
            const badges = {
                'pending': '<span class="badge bg-secondary">等待中</span>',
                'processing': '<span class="badge bg-info">处理中</span>',
                'completed': '<span class="badge bg-success">已完成</span>',
                'failed': '<span class="badge bg-danger">失败</span>'
            };
            return badges[status] || status;
        }
        
        // 获取任务操作按钮
        function getJobActions(job) {
            let html = '';
            
            if (job.status === 'completed' && job.download_url) {
                html += `<a href="${job.download_url}" class="btn btn-sm btn-success">下载</a> `;
            }
            
            if (job.status === 'failed') {
                html += `<button class="btn btn-sm btn-outline-danger" 
                         onclick="showJobError('${job.id}')">查看错误</button>`;
            }
            
            if (job.status === 'pending' || job.status === 'processing') {
                html += `<span class="text-muted">处理中...</span>`;
            }
            
            return html;
        }
        
        // 显示任务错误
        function showJobError(jobId) {
            fetch(`/LabDatabase/export/`)
                .then(response => response.json())
                .then(jobs => {
                    const job = jobs.find(j => j.id === jobId);
                    if (job && job.error_message) {
                        Swal.fire({
                            title: '导出失败',
                            text: job.error_message,
                            icon: 'error',
                            confirmButtonText: '确定'
                        });
                    }
                });
        }
        
        // 加载导出历史
        function loadExportHistory() {
            alert('加载导出历史');
            // fetch('/admin/api/exporthistory/')
            //     .then(response => response.json())
            //     .then(jobs => {
            //         const tbody = document.getElementById('exportHistoryBody');
            //         tbody.innerHTML = '';
                    
            //         if (jobs.length === 0) {
            //             tbody.innerHTML = `
            //                 <tr>
            //                     <td colspan="6" class="text-center py-5 text-muted">
            //                         <i class="bi bi-clock-history fs-1"></i>
            //                         <p class="mt-3">暂无导出记录</p>
            //                     </td>
            //                 </tr>
            //             `;
            //             return;
            //         }
                    
            //         jobs.forEach(job => {
            //             const filters = job.filters || {};
            //             const filterText = [];
                        
            //             if (filters.start_date) {
            //                 filterText.push(`从 ${formatDate(filters.start_date)}`);
            //             }
            //             if (filters.end_date) {
            //                 filterText.push(`到 ${formatDate(filters.end_date)}`);
            //             }
            //             if (filters.user_ids && filters.user_ids.length > 0) {
            //                 filterText.push(`${filters.user_ids.length}个用户`);
            //             }
            //             if (filters.component_types && filters.component_types.length > 0) {
            //                 filterText.push(`${filters.component_types.length}种类型`);
            //             }
                        
            //             const row = document.createElement('tr');
            //             row.dataset.jobId = job.id;
                        
            //             row.innerHTML = `
            //                 <td>${job.filename}</td>
            //                 <td>${formatDateTime(job.created_at)}</td>
            //                 <td class="job-size">${job.file_size ? formatFileSize(job.file_size) : '-'}</td>
            //                 <td class="job-status">${getJobStatusBadge(job.status)}</td>
            //                 <td>${filterText.join(' | ') || '全部数据'}</td>
            //                 <td class="job-actions">${getJobActions(job)}</td>
            //             `;
                        
            //             tbody.appendChild(row);
            //         });
            //     })
            //     .catch(error => {
            //         console.error('加载导出历史失败:', error);
            //         showError('加载导出历史失败');
            //     });
        }
        
        // 导出单个用户数据
        async function exportUserData(userId) {
            console.log(userId);
            // window.location.href = `/LabDatabase/exportUserData/${userId}`;
            const response = await fetch(`/LabDatabase/exportUserData/${userId}`);
            const result = await response.json();
            // const result = await response.json()
            if(result.task_id){
                alert(result.message);
                pollTaskStatus(result.task_id);
            }
            else{
                displayResult(result);
            }
        }
        
        // 导出用户统计
        async function exportUserStats() {
            const response = await fetch(`/LabDatabase/exportallData`);
            const result = await response.json();
            console.log(result);
            if(result.task_id){
                alert(result.message);
                pollTaskStatus(result.task_id);
            }
            else{
                displayResult(result);
            }
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
                    alert("上传完成")
                }
            }
            else{
                alert('处理失败：'+result.error)
            }
        }
            // fetch(`/LabDatabase/user-stats/?${params}`)
            //     .then(response => response.json())
            //     .then(data => {
            //         // 创建CSV数据
            //         const csvContent = createUserStatsCSV(data.users);
                    
            //         // 下载文件
            //         downloadCSV(csvContent, `用户统计_${new Date().toISOString().slice(0, 10)}.csv`);
                    
            //         hideLoading();
            //         showSuccess('用户统计导出成功');
            //     })
            //     .catch(error => {
            //         console.error('导出用户统计失败:', error);
            //         hideLoading();
            //         showError('导出用户统计失败');
            //     });
        // }

        function pollTaskStatus(taskId){
            const pollInterval = setInterval(async () => {
                    try {
                        const response = await fetch(`/LabDatabase/excel_task_status/${taskId}`);
                        const contentType = await response.headers.get('content-type');
                        console.log(contentType);
                        // if(contentType.toString() !== "application/json"){
                        //     console.log("completed");
                        //     clearInterval(pollInterval);
                        //     alert("导出完成");
                        // }
                        
                            const result = await response.json();
                            console.log(result);
                            if(result.status === "completed"){
                                console.log("completed");
                                clearInterval(pollInterval);
                                displayResult(result);
                                window.location.href = `/LabDatabase/getDocument/${result.file_id}`;
                            }
                            else if(result.status === "failed"){
                                clearInterval(pollInterval);
                                displayError(result.message);
                            }
                    }
                    catch(error){
                        clearInterval(pollInterval);
                        displayError('轮询失败：'+error.message);
                    }
                }, 2000);
        }
        
        // 创建用户统计CSV
        // function createUserStatsCSV(users) {
        //     const headers = ['用户名', '邮箱', '姓名', '注册时间', '最后登录',
        //                    '总上传数', '已通过', '待审核', '已拒绝', '最后上传时间'];
            
        //     let csv = headers.join(',') + '\n';
            
        //     users.forEach(user => {
        //         const row = [
        //             user.username,
        //             user.email,
        //             `${user.first_name || ''} ${user.last_name || ''}`.trim(),
        //             formatDateTime(user.date_joined),
        //             user.last_login ? formatDateTime(user.last_login) : '从未登录',
        //             user.total_components,
        //             user.approved_components,
        //             user.pending_components,
        //             user.rejected_components,
        //             user.last_upload_time ? formatDateTime(user.last_upload_time) : '从未上传'
        //         ].map(field => `"${field}"`).join(',');
                
        //         csv += row + '\n';
        //     });
            
        //     return csv;
        // }
        
        // 下载CSV文件
        function downloadCSV(content, filename) {
            const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
        }
        
        // 辅助函数
        function showLoading(message = '正在处理...') {
            document.getElementById('loadingMessage').textContent = message;
            document.getElementById('loadingOverlay').style.display = 'flex';
        }
        
        function hideLoading() {
            document.getElementById('loadingOverlay').style.display = 'none';
        }
        
        function showSuccess(message) {
            Swal.fire({
                title: '成功',
                text: message,
                icon: 'success',
                confirmButtonText: '确定'
            });
        }
        
        function showError(message) {
            Swal.fire({
                title: '错误',
                text: message,
                icon: 'error',
                confirmButtonText: '确定'
            });
        }
        
        function formatDateTime(dateTimeStr) {
            if (!dateTimeStr) return '';
            const date = new Date(dateTimeStr);
            return date.toLocaleString('zh-CN');
        }
        
        function formatDate(dateStr) {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return date.toLocaleDateString('zh-CN');
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function getCSRFToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        }