from django.urls import path
from .views import(add_entity, get_entity, register_user,login_user,
    list_user_trips, create_trip, get_trip_details, update_or_delete_trip,
    get_recent_trip, list_log_details_for_trip,
    get_trip_detail, create_trip_detail, update_or_delete_trip_detail,
    get_log_detail, create_log_detail, update_or_delete_log_detail
 ,get_trip, log_book_detail_view, log_book_view,create_activity_log,
 delete_activity_log, log_summary,get_activity_log
 )

urlpatterns = [

    # Trip Endpoints
    path('trips/', list_user_trips, name='list_user_trips'),
    path('trips/create/', create_trip, name='create_trip'),
    path('trips/<int:trip_id>/', get_trip_details, name='get_trip_details'),
    path('trips/<int:trip_id>/update/', update_or_delete_trip, name='update_trip'),
    path('trips/recent/', get_recent_trip, name='get_recent_trip'),
    path('trips/edit/<int:trip_id>/',get_trip,name = 'get_trip'),
    # TripDetail Endpoints
    path('trips/<int:trip_id>/detail/', get_trip_detail, name='get_trip_detail'),
    path('trips/<int:trip_id>/detail/create/', create_trip_detail, name='create_trip_detail'),
    path('trips/detail/update/<int:trip_id>/', update_or_delete_trip_detail, name='update_trip_detail'),
    
    # LogDetail Endpoints
    path('trips/<int:trip_id>/logs/', list_log_details_for_trip, name='list_log_details'),
    path('trips/<int:trip_id>/log/', get_log_detail, name='get_log_detail'),
    path('trips/<int:trip_id>/log/create/', create_log_detail, name='create_log_detail'),
    path('trips/<int:trip_id>/log/update/', update_or_delete_log_detail, name='update_log_detail'),

    #LogBook Endpoints 
    path('log-books/<int:log_detail_id>/', log_book_view, name='log_book'),
    path('log-books/<int:log_detail_id>/detail/', log_book_detail_view, name='log_book_detail'),
    

    # Activity Log Endpoints
    path('log-books/<int:log_book_id>/activity-logs/', create_activity_log, name='create_activity_log'),
    path('log-books/<int:log_book_id>/activity-logs/<int:activity_log_id>/', delete_activity_log, name='delete_activity_log'), # Added comma here
    path('log-summary/<int:log_detail_id>/',log_summary, name ='log_summary'),
     path('get-activity-log/<int:log_book_id>/', get_activity_log, name='get_activity_log'),

    #User Auth endpoints 
    path('add-entity/', add_entity, name='add_entity'),
    path('get-entity/', get_entity, name='get_entity'),
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
]