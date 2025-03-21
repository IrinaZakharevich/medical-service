from django.urls import path
from .views import RefbookListView, RefbookItemListView, RefbookItemValidationView

urlpatterns = [
    path('refbooks/', RefbookListView.as_view(), name='refbooks-list'),
    path('refbooks/<int:id>/elements/', RefbookItemListView.as_view(), name='refbook-list-items'),
    path('refbooks/<int:id>/check_element/', RefbookItemValidationView.as_view(), name='refbook-check-item'),
]
