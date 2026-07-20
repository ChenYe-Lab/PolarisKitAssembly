from django.urls import path
from . import views

urlpatterns = [
    path("landing", views.landing_page, name="landing"),
    path("index",views.index,name = "index"),
    path("register_vistor", views.register_visitor, name="register_vistor"),
    path("register_visitor", views.register_visitor, name="register_visitor"),
    path("track_visit", views.track_visit, name="track_visit"),
    path("submit_feedback", views.submit_feedback, name="submit_feedback"),
    path("initdata",views.InitData, name="initdata"),
    path("assembly",views.Assembly,name = "assembly"),
    path("task_status/<str:taskID>",views.task_status,name="task_status"),
    path("getAssembly/<str:taskID>/<str:name>",views.getAssembly,name="getAssembly"),
    path("gg_assemble",views.gg_assemble,name="gg_assemble"),
    path("getTutorial",views.getTutorial,name="getTutorial"),
    path("getZip",views.getZip,name="getZip"),
    path("toturial",views.getTutorialTest,name="toturial"),
    path("toturial/<path:doc_path>", views.getTutorialTest, name="toturial_doc"),
]
