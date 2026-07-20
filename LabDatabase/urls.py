from django.urls import path,include
from rest_framework.routers import DefaultRouter
from LabDatabase.AdminManage import admin_views
from LabDatabase import views,admin
from .CaculateModule import DNADiagram
urlpatterns = [
    #index
    path("index",views.index,name="index"),
    path("design-builder", views.design_builder, name="design_builder"),
    path("design-builder/gene-search", views.design_gene_search, name="design_gene_search"),
    path("design-builder/submit", views.submit_design_assembly, name="submit_design_assembly"),
    path("getdata",views.getData,name="getData"),
    path("filterdata",views.DataFilter,name="filterdata"),
    #user
    path("login",admin.login,name="login"),
    path("logout",admin.logout,name="logout"),
    path("register",admin.register,name="register"),
    path("AdminRegister",admin.register_admin, name = "AdminRegister"),

    

    #Upload Sequence Map
    path("UploadMap",views.UploadMap,name="UploadMap"),
    path("CheckAndFixGenBank", views.CheckAndFixGenBank, name="CheckAndFixGenBank"),
    path("CustomScar", views.CustomScar, name="CustomScar"),



    #Upload Excel File
    path("UploadFile",views.UploadFile,name="UploadFile"),
    path("task_status/<str:task_id>",views.task_status,name="task_status"),
    path("excel_task_status/<str:task_id>",views.excel_task_status,name= "excel_task_status"),
    #Search Information
    path("part/<int:partid>",views.part_detail_show,name="part_detail"),
    path("backbone/<int:backboneid>",views.backbone_detail_show,name="backbone_detail"),
    path("plasmid/<int:plasmidid>",views.plasmid_detail_show,name="plasmid_detail"),

    #delete
    path("deletepart",views.delete_part,name="delete_part"),
    path("deletebackbone",views.delete_backbone,name="delete_backbone"),
    path("deleteplasmid",views.delete_plasmid,name="delete_plasmid"),

    #Modify
    path("modifypart/<int:partid>",views.modify_part,name="modify_part"),
    path("modifybackbone/<int:backboneid>",views.modify_backbone, name="modify_backbone"),
    path("modifyplasmid/<int:plasmidid>",views.modify_plasmid,name="modify_plasmid"),

    #download templates
    path("download/<str:type>",views.download_template,name="downloadtemplate"),
    
    #download part map
    path("downloadPlasmidMap/<int:plasmidid>",views.downloadPlasmidMap,name="downloadPlasmidMap"),
    path("downloadBackboneMap/<int:backboneid>",views.downloadBackboneMap,name="downloadBackboneMap"),
    path("downloadPartMap/<int:partid>",views.downloadPartMap,name="downloadPartMap"),
    
    path("adminPage",admin_views.AdminDashbordView, name = "adminPage"),
    path("exportUserData/<str:username>",views.exportuserdata,name="exportuserdata"),
    path("exportallData",views.ExportAllData,name="exportallData"),
    path("getDocument/<str:fileid>",views.getDocument,name="getDocument"),
    path("getDocByAdd",views.getDocumentByAddress,name="getDocByAdd"),
    path("getAssembly/<str:fileName>",views.getAssemblyFile,name="getAssembly"),
    path("getAssemblyArchive/<str:task_id>",views.getAssemblyArchive,name="getAssemblyArchive"),
    
    path("createRepo",views.CreateTempRepository,name="createRepo"),
    path("AssemblyRepo",views.AssemblyRepo,name="AssemblyRepo"),
    # path("createRepoAndBatchAssembly",views.createRepoAndBatchAssembly,name="createRepoAndBatchAssembly"),
    
    path("AssemblyWithoutRepo",views.AssemblyWithoutRepo,name="AssemblyWithoutRepo"),
    
    path("FetchExperienceDetail/<str:partName>",views.GetExperienceDetail,name="FetchExperienceDetail"),
    path("api/upload/view",views.view_upload_records,name="view_upload_records"),
    
    path("user/<str:username>",views.user,name="user"),
    
    path("GetParent",views.GetParentInfo,name="GetParent"),
    
    path("RepositoryDiagram/<str:repositoryName>",DNADiagram.generate_plasmid_view,name="RepositoryDiagram"),
    path("ShowRepository/<str:repositoryName>",views.showRepository,name="ShowRepository"),
]
