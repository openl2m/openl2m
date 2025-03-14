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
from django.shortcuts import render
from django.views import View

from switches.utils import dprint


#
# Class MyView() extends Django's View() class to add a better "unknown method" handler.
#
class MyView(View):

    # we only override this handler, which throws an Exception in the View() class.
    def http_method_not_allowed(self, request, **args):
        # return HttpResponse(
        #     "Method not allowed. Allowed methods: " + ", ".join(allowed_methods),
        #     status=405
        # )
        dprint("MyView.http_method_not_allowed() called")
        return render(request=request, template_name="405.html", status=405)
