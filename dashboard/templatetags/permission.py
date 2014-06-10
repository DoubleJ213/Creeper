# Copyright 2012 Beixinyuan(Nanjing), All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from django import template
from django.core.urlresolvers import reverse
from django.db import connection
from django.utils.translation import ugettext

register = template.Library()


class PermissionNode(template.Node):
    def __init__(self, rights, node_list, opt):
        self.rights = rights
        self.node_list = node_list
        self.opt = opt

    def render(self, context):
        # current request from context
        request = context.get('request', None)
        if not request:
            return ""
        if self.opt == 'or':
            for right in self.rights:
                right = self.translate(right, context)
                # check permission from request or db
                if has_right(get_user_role_id(request), right):
                    return self.node_list[0].render(context)

            return "" if not self.otherwise else self.node_list[-1].render(
                context)
        else:
            for right in self.rights:
                right = self.translate(right, context)
                # check permission from request or db
                if not has_right(get_user_role_id(request), right):
                    return "" if not self.otherwise else self.node_list[
                                                         -1].render(context)

            return self.node_list[0].render(context)

    def translate(self, right, context):
        if not (right[0] == right[-1] and right[0] in ('"', "'")):
            return template.Variable(right).resolve(context)
        else:
            return right[1: -1]

    @property
    def otherwise(self):
        return len(self.node_list) > 1


class MenuNode(template.Node):
    def render(self, context):
        request = context.get('request', None)
        if not request:
            return ""

        rows = get_menu()

        index_mapping = {row['id']: row for index, row in enumerate(rows)}
        # walk all menu records and build the tree.
        for row in rows:
            # top level menu
            # here we can kick off some menus with permission.
            if row['parent_id'] == -1:
                if row.has_key('children'):
                    continue
                else:
                    row['children'] = []
            else:
                if not has_right(get_user_role_id(request), row['token']):
                    continue
                parent_row = index_mapping[row['parent_id']]
                if parent_row.get('children', None) == None:
                    parent_row['children'] = []
                parent_row['children'].append(row)
                row['save'] = False

        # filter leave nodes and non-children nodes
        rows = filter(lambda x: x.pop('save', True) and x.get('children', []),
                      rows)

        top_template = "<div class='accordionHeader'><h2><span>Folder</span"\
                       ">%s</h2></div>"
        accordion_template = "<div class='accordionContent'><ul "\
                             "class='tree'>%s</ul></div>"
        child_template = "<li><a href='%s' target='navTab' rel='%s'>%s</a></li>"
        html = ""
        
        for row in rows:
            label_name = ugettext(row['label_name'])
            html += top_template % label_name
            child_html = ''.join([child_template % (
                reverse(child['action_name']),
                ugettext(child['label_name']),
                ugettext(child['label_name']))
                                  for child in row['children']])
            html += (accordion_template % child_html)

        return html


@register.tag(name='permission')
def do_permission(parser, token):
    """
    permission tags for templates. At first, you must load custome tags from
    templatetags by {% load permission %}, and then use like following examples.

    A single block tags for check permission and display the context between
    them.

    ::

    {% permission 'right name' %}
        something want to be hidden if user does not have right
    {% endpermission %}


    A block tags with 'otherwise' that just like 'if-else' to choose which
    context to be displayed

    ::

    {% permission variable_from_request_context %}
        something want to be hidden if user does not have right
    {% otherwise %}
        show some warning tips or just leave it empty.
    {% endpermission %}


    """
    context = token.split_contents()
    if len(context) < 2:
        raise template.TemplateSyntaxError(
            "%r tag requires one right name at least" % token.contents.split()[
                                                        0])

    rights = context[1:]
    nodelist = [parser.parse(('otherwise', 'endpermission'))]
    token = parser.next_token()

    # {% otherwise %}
    if token.contents == 'otherwise':
        nodelist.append(parser.parse(('endpermission',)))
        token = parser.next_token()

    # {% endpermission %}
    assert token.contents == 'endpermission'

    opt = 'and'
    if len(rights) == 1:
        filter_rights = rights
    else:
        l = len(rights)
        i = 0
        filter_rights = list()
        while i < l:
            token = rights[i]
            if token in ('or', 'and'):
                opt = token
            else:
                filter_rights.append(token)
            i += 1

    return PermissionNode(filter_rights, nodelist, opt)


@register.tag(name='ui:menu')
def do_menu(parser, token):
    """
    Creeper UI tags for generate menu.
    """
    context = token.split_contents()
    if len(context) > 1:
        raise template.TemplateSyntaxError(
            "%r tag does not require any arguments" % token.contents.split()[
                                                      0])

    return MenuNode()


def has_right(role_id, right_name):
    """

    """
    cursor = connection.cursor()
    cursor.execute('SELECT depends FROM rights r, role_right t '
                   'WHERE t.role_id = %s '
                   'AND t.right_key = r.key '
                   'AND r.name = %s', [role_id, right_name])
    row = cursor.fetchone()

    if not row:
        return False
    else:
        depends = json.loads(row[0])
        if not depends or not depends.has_key('depend_keys'):
            return True
        right_ids = depends.pop('depend_keys')
        if not right_ids:
            return True
        right_nums = len(right_ids)
        sql = 'SELECT 1 FROM rights r, role_right t '\
              'WHERE t.role_id = %s '\
              'AND t.right_key = r.key '\
              'AND r.key in ('
        for num in range(right_nums):
            sql += '%s,'
        sql = sql[:-1] + ')'
        right_ids.insert(0, role_id)
        rows = cursor.execute(sql, right_ids)
        return rows == right_nums


def get_menu(action_type='menu', role='admin'):
    cursor = connection.cursor()
    cursor.execute('SELECT id, label_name, action_name, action_type, '
                   'role, parent_id, token FROM control_manage_controller '
                   'WHERE role=%s AND action_type=%s',
                   [role, action_type])
    desc = cursor.description
    # convert tuple to dict with column name
    rows = [dict(zip([col[0] for col in desc], row)) for row in
            cursor.fetchall()]

    return rows

ROLE_ADMIN = 'admin'

def get_user_role_id(request):
    role_id = ''

    for role in request.user.roles:
        if role['name'] != ROLE_ADMIN:
            role_id = role['id']
            break
        else:
            role_id = role['id']

    return role_id
