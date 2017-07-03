from django.conf.urls import include, url

from ..views import default


urls = [
    url(
        r'^questionnaire/forms/$',
        default.PDFFormList.as_view(),
        name='pdf_form_list'),
    url(
        r'^questionnaire/forms/new/$',
        default.PDFFormAdd.as_view(),
        name='pdf_form_add'),
    url(
        r'^questionnaire/forms/(?P<form>[-\w]+)/$',
        default.PDFFormDetails.as_view(),
        name='pdf_form_view'),
    url(
        r'^questionnaire/forms/(?P<form>[-\w]+)/edit/$',
        default.PDFFormEdit.as_view(),
        name='pdf_form_edit'),
    url(
        r'^questionnaire/forms/(?P<form>[-\w]+)/download/$',
        default.PDFFormDownload.as_view(),
        name='pdf_form_download'),
    url(
        r'^questionnaire/forms/(?P<form>[-\w]+)/delete/$',
        default.PDFFormDelete.as_view(),
        name='pdf_form_delete'),
]

urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/',
        include(urls)),
]
