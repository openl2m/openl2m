.. image:: ../../_static/openl2m_logo.png

===============
The notices app
===============

The *notices/* directory contains a really simple app to administratively add some system notices. This is pretty much standard Django.

This shows up under the Admin interface, and allows you to add system notices that are enabled for a specific time window.


**models.py**
We define the very simple Notice() class here. This has a Django object manager (NoticeManager()) that allows
for easy querying active notices.

**apps.py** defines the application (standard Django), and **admin.py** registers this into the main admin site.


**Implementation**

Notices are called when users get the main menu, i.e. right after they login, or go back to the menu.

This is implemented in the switches application, in *switches/views.py*, in the *def switches()* function.
Notices are added to the *messages* variable, which uses the Django message frame work (see https://docs.djangoproject.com/en/4.1/ref/contrib/messages/)

.. code-block:: python3

    # are there any notices to users?
    notices = Notice.objects.active_notices()
    if notices:
        for notice in notices:
            messages.add_message(request=request, level=notice.priority, message=notice.content)

In the *templates/_base.html* template, available messages are listed with the following code fragment. This actually allows messages
to be posted on *any* page, if the *messages* variable has content in it. At present, this is only used when the main menu is called.


.. code-block:: jinja

    {% for message in messages %}
        <div class="alert alert-{{ message.tags }} text-center" role="alert">
            <i class="fas fa-exclamation-triangle"></i>&nbsp;<bold>{{ message }}</bold>&nbsp;<i class="fas fa-exclamation-triangle"></i>
        </div>
    {% endfor %}
