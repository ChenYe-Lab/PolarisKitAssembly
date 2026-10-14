// document.addEventListener('DOMContentLoaded',function(){

        // })
        document.getElementById('downPartMapButton').addEventListener('click',function(){
            let pathname_list = window.location.pathname.split('/');
            let partid = pathname_list[pathname_list.length -1];
            console.log(partid);
            window.location.href = `/LabDatabase/downloadPartMap/${partid}`;
        })

        document.getElementById("getExperienceData").addEventListener('click',function(){
            let partName = document.getElementById("gene-name-div").innerText.split('(')[0];
            console.log(partName);
            window.location.href = `/LabDatabase/FetchExperienceDetail/${partName}`;
        })