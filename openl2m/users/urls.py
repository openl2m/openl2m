#
# This file is part of Open Layer 2 Management (OpenL2M).
#
# OpenL2M is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with OpenL2M. If not, see <http://www.gnu.org/licenses/>.
#
from django.urls import path

from . import views

app_name = 'users'
urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('info/<int:user_id>/', views.InfoView.as_view(), name='info'),
    path('tokens/', views.TokenListView.as_view(), name='token_list'),
    path('tokens/add/', views.TokenAdd.as_view(), name='token_add'),
    path('tokens/edit/<int:token_id>/', views.TokenEdit.as_view(), name='token_edit'),
    path('tokens/delete/<int:token_id>/', views.TokenDelete.as_view(), name='token_delete'),
    #    path('tokens/<int:pk>/', include(get_model_urls('users', 'token'))),
]
