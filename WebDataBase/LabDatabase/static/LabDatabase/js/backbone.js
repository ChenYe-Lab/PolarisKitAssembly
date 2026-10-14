
            const plasmid_map_div = document.getElementById("plasmid-map-div");
            
            // '<div class="plasmid-label" style="transform: rotate(0deg) translate(220px) rotate(0deg);">{{backbone.marker}}</div>'
            // '<div class="plasmid-label" style="transform: rotate(90deg) translate(220px) rotate(-90deg);">{{backbone.ori}}</div>'
            ori_list = document.getElementById('ori_detail_content').innerText.split(',');
            marker_list = document.getElementById('marker_detail_content').innerText.split(',');
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
            // 简单的载体图谱交互效果
        document.querySelectorAll('.plasmid-label').forEach(label => {
            label.addEventListener('mouseover', function() {
                this.style.backgroundColor = 'rgba(255,255,255,0.7)';
                this.style.padding = '2px 5px';
                this.style.borderRadius = '3px';
                this.style.zIndex = '10';
            });
            
            label.addEventListener('mouseout', function() {
                this.style.backgroundColor = 'transparent';
                this.style.padding = '0';
                this.style.borderRadius = '0';
                this.style.zIndex = '1';
            });
        });
        document.getElementById('downPartMapButton').addEventListener('click',function(){
            let pathname_list = window.location.pathname.split('/');
            let backboneid = pathname_list[pathname_list.length -1];
            window.location.href = `/LabDatabase/downloadBackboneMap/${backboneid}`;
        })
        
        
        // 下载按钮交互
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', function() {
                const originalText = this.innerHTML;
                this.innerHTML = '<i>✓</i> 下载中...';
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                    alert('下载完成！');
                }, 1500);
            });
        });