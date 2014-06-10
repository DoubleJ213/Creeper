__author__ = 'liuh'

import logging

LOG = logging.getLogger(__name__)

import md5
from datetime import datetime

from models import NeedToDo
from dashboard.authorize_manage import ROLE_ADMIN, ROLE_MEMBER, ROLE_PROJECTADMIN
from dashboard import api
from dashboard.exceptions import Unauthorized
from dashboard.authorize_manage.utils import get_user_role_name, switch_tenants
#############################################################################

#STATUS DEFINE
STATUS_NEW = 'new'
STATUS_DOING = 'doing'
STATUS_DONE = 'done'
STATUS_CLOSED = 'closed'

STATUS = [STATUS_NEW, STATUS_DOING, STATUS_DONE, STATUS_CLOSED]
STATUS_TO_DO = [STATUS_NEW, STATUS_DOING]

#BASE CLASS DEFINE
class BasePrepareMeta(type):
    def __new__(mcs, name, bases, attrs):
        # Process options from Meta
        _meta = attrs.get("Meta", None)
        if not _meta:
            raise AttributeError()
        if not (getattr(_meta, 'title', None) and
                getattr(_meta, 'parameters', None) and
                getattr(_meta, 'content', None) and
                getattr(_meta, 'work_func', None) and
                getattr(_meta, 'category', None) and
                getattr(_meta, 'role', None) and
                getattr(_meta, 'tenant_id', None) and
                getattr(_meta, 'prepare_id', None)
            ):
            raise AttributeError()

        attrs["_meta"] = _meta
        return type.__new__(mcs, name, bases, attrs)

# BASE CLASS DEFINE
class BasePrepare(object):
    # title

    __metaclass__ = BasePrepareMeta

    def __init__(self, uuid, role, tenant_id, prepare_id, *arg):
        if uuid:
            self._obj = NeedToDo.objects.get(need_uuid=uuid)
        else:
            self._obj = self.create_need_to_do(role, tenant_id, prepare_id,
                                               *arg)

    def create_need_to_do(self, role, tenant_id, prepare_id, *arg):
        try:
            title = self._meta.title
            parameters = ''
            if arg is not None or arg != '':
                parameters = arg
            content = self._meta.content

            if role != '' and role is not None:
                self._meta.role = role
            if tenant_id != '' and tenant_id is not None:
                self._meta.tenant_id = tenant_id
            if prepare_id != '' and prepare_id is not None:
                self._meta.tenant_id = prepare_id

            created_at = datetime.now().utcnow()
            uuid = md5.new(str(created_at)).hexdigest()
            need_to_do = NeedToDo(need_uuid=uuid, title=title,
                                  parameters=parameters,
                                  content=content,
                                  work_func=self._meta.work_func,
                                  category=self._meta.category,
                                  status=STATUS_NEW,
                                  role=self._meta.role,
                                  tenant_id=self._meta.tenant_id,
                                  prepare_id=self._meta.prepare_id)
            need_to_do.save()
            return need_to_do
        except TypeError, exc:
            self._obj = None
            LOG.error("arguments set failed, error is %s" % exc)
        except Exception, exc:
            LOG.error("create NeedToDo failed, error is %s " % exc)

        return None

    @property
    def title(self):
        return getattr(self._obj, 'title', None) if self._obj else None

    @property
    def parameters(self):
        return getattr(self._obj, 'parameters', None) if self._obj else None

    @property
    def content(self):
        return getattr(self._obj, 'content', None) if self._obj else None

    @property
    def work_func(self):
        return getattr(self._obj, 'work_func', None) if self._obj else None

    @property
    def category(self):
        return getattr(self._obj, 'category', None) if self._obj else None


    def status(self, request):
        if self.update_status(request, self._meta.tenant_id, self._meta.parameters):
            self.close()
        return getattr(self._obj, 'status', None) if self._obj else None

    @property
    def role(self):
        return getattr(self._obj, 'role', None) if self._obj else None

    @property
    def tenant_id(self):
        return getattr(self._obj, 'tenant_id', None) if self._obj else None

    @property
    def prepare_id(self):
        return getattr(self._obj, 'prepare_id', None) if self._obj else None


    def prepare(self, request):
        return self.prepare_list(request, self._obj.prepare_id)

    # action
    def renew(self):
        """
        :return: True indicate action success, otherwise False indicate action failed
        """
        return self._action(STATUS_NEW)

    def begin(self):
        """
        :return: True indicate action success, otherwise False indicate action failed
        """
        return self._action(STATUS_DOING)

    def end(self):
        """
        :return: True indicate action success, otherwise False indicate action failed
        """
        return self._action(STATUS_DONE)

    def close(self):
        """
        :return: True indicate action success, otherwise False indicate action failed
        """
        return self._action(STATUS_CLOSED)

    def _action(self, status):
        """
        :return: True indicate action success, otherwise False indicate action failed
        """
        if self._obj:
            try:
                self._obj.status = status
                self._obj.save()
                return True
            except Exception, e:
                LOG.debug(
                    "BasePrepare update status (%s) failed, error is %s" % (
                        status, e))
        return False

    def update_status(self, request, tenant_id, parameters):
        pass

    def prepare_list(self, request, prepare_id):
        pass

    @staticmethod
    def list():
        """
        :return: List<BasePrepare>  indicate success,
                 None               indicate action Failed
        """
        try:
            need_list = NeedToDo.objects.order_by("create_at").all()
            return [BasePrepare(None, need) for need in need_list]
        except Exception, exc:
            LOG.error("BasePrepare get list failed,error is :%s" % exc)
        return None

    class Meta:
        title = 'base'
        parameters = 'base'
        content = 'base'
        work_func = 'base'
        category = 'prepare_manage'
        role = ROLE_MEMBER
        tenant_id = 'admin'
        prepare_id = 'base'

#define your Customer Prepare Class here

class CreateTenantPrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'Please create your first tenant',
        'content': 'abc',
        'work_func': 'create_project_need',
        'category': 'project_manage',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """

    def update_status(self, request, tenant_id ,parameters):
        projects = []
        try:
            projects = api.tenant_list(request, admin=True)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error(e)
            return False

        if len(projects) > 0:
            return True
        else:
            return False

    class Meta:
        title = 'Please create your first tenant'
        parameters = 'Please create your first tenant'
        content = 'Please create your first tenant'
        work_func = 'create_project_need_form'
        category = 'project_manage'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateTenantPrepare, self).__init__(uuid, role, tenant_id,
                                                  prepare_id, *arg)

from dashboard.usage.quotas import tenant_quota_usages

class CreateTenantResourcesShortagePrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'The quotas of the tenant(%s) will be shortage(%s), handle please',
        'content': '',
        'work_func': '',
        'category': 'project_manage_resource',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """

    def update_status(self, request, tenant_id ,parameters):
        try:
            usages = tenant_quota_usages(request)
            usages_update = ''
            if usages is not None:
                if usages_attribute(usages['cores']):
                    usages_update += 'cores'
                if usages_attribute(usages['instances']):
                    usages_update += 'instances'
                if usages_attribute(usages['volumes']):
                    usages_update += 'volumes'
                if usages_attribute(usages['gigabytes']):
                    usages_update += 'gigabytes'
                if usages_attribute(usages['ram']):
                    usages_update += 'ram'
                if usages_attribute(usages['floating_ips']):
                    usages_update += 'floating_ips'
            if len(usages_update) > 0:
                return True
        except Exception, exc:
            LOG.info('Error is :%s' % exc)
            return False

    def prepare_list(self, request, prepare_id):
        pass

    class Meta:
        title = 'The quotas of the tenant(%s) will be shortage(%s), handle please'
        parameters = 'The quotas of the tenant(%s) will be shortage(%s), handle please'
        content = 'The quotas of the tenant(%s) will be shortage(%s), handle please'
        work_func = 'update_project_quotas_form_index'
        category = 'project_manage_resource'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateTenantResourcesShortagePrepare, self).__init__(uuid, role,
                                                                   tenant_id,
                                                                   prepare_id,
                                                                   *arg)


class CreateVolumePrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'The volume of the storage disk will be shortage(%s|%s), handle please',
        'content': '',
        'work_func': '',
        'category': '',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """
    def update_status(self, request, tenant_id ,parameters):

        try:
            usages = tenant_quota_usages(request)
            usages_update = False
            if usages is not None:
                if usages_attribute(usages['gigabytes']):
                    usages_update = True
            return usages_update
        except Exception, exc:
            LOG.info('Error is :%s' % exc)
            return False

    def prepare_list(self, request, prepare_id):
        pass

    class Meta:
        title = 'The volume of the storage disk will be shortage(%s|%s), handle please'
        parameters = 'The volume of the storage disk will be shortage(%s|%s), handle please'
        content = 'The volume of the storage disk will be shortage(%s|%s), handle please'
        work_func = 'volume_quotas_tab_init'
        category = 'volume_manage'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateVolumePrepare, self).__init__(uuid, role, tenant_id,
                                                  prepare_id, *arg)


class CreateVirtualNetworkPrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'Please create your first net and add one sub for it',
        'content': '',
        'work_func': '',
        'category': 'virtual_network_manage',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """

    def update_status(self, request, tenant_id ,parameters):
        projects = []
        try:
            projects = api.tenant_list(request, admin=True)
        except Unauthorized:
            raise
        except Exception, exe:
            LOG.error('Unable to retrieve project list,%s.' % exe.message)
            return False
        networks = []
        for project in projects:
            if project.enabled:
                try:
                    network_list = api.quantum.network_list_for_tenant(request,
                                                                       project.id)
                except Unauthorized:
                    raise
                if network_list:
                    for network in network_list:
                        networks.append(network)

        if len(networks) > 0:
            return True
        return False

    def prepare_list(self, request, prepare_id):
        sub_nets = api.quantum.subnet_list(request,
                                           network_id=prepare_id)

        for s in sub_nets:
            s.set_id_as_name_if_empty()

        if len(sub_nets) > 0:
            return True
        return False

    class Meta:
        title = 'Please create your first net and add one sub for it'
        parameters = 'Please create your first net and add one sub for it'
        content = 'Please create your first net and add one sub for it'
        work_func = 'create_network_index_prepare'
        category = 'virtual_network_manage'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateVirtualNetworkPrepare, self).__init__(uuid, role, tenant_id,
                                                          prepare_id, *arg)

#
class CreateVirtualRouterPrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'Please create your first router and organizing the first gateway',
        'content': '',
        'work_func': '',
        'category': 'virtual_router_manage',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """

    def update_status(self, request, tenant_id ,parameters):
        tenants = []
        try:
            tenants = api.tenant_list(request, admin = True)
        except Exception,exc:
            msg = 'Unable to retrieve project list,%s.' % exc
            LOG.error(msg)
            return False
        router_projects = []
        for project in tenants:
            if project.enabled and None != switch_tenants(request, project.id):
                router_project_list = api.quantum.router_list(request)
                if router_project_list:
                    for routerProject in router_project_list:
                        if project.id == routerProject.tenant_id:
                            router_projects.append(routerProject)

        if len(router_projects) > 0:
            return True

        return False

    def prepare_list(self, request, prepare_id):
        ports = api.quantum.port_list(request, device_id=prepare_id)

        for port in ports:
            port.set_id_as_name_if_empty()

        if len(ports) > 0:
            return True
        return False

    class Meta:
        title = 'Please create your first router and organizing the first gateway'
        parameters = 'Please create your first router and organizing the first gateway'
        content = 'Please create your first router and organizing the first gateway'
        work_func = 'create_router_detail_index'
        category = 'virtual_router_manage'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateVirtualRouterPrepare, self).__init__(uuid, role, tenant_id,
                                                         prepare_id, *arg)


class CreateServerResourceShortagePrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'The resources of the server will be shortage, handle please',
        'content': '',
        'work_func': '',
        'category': '', },
    """

    def update_status(self, request, tenant_id ,parameters):
        try:
            para = parameters[2:-2].split("', '")
            facility_list = api.nova.get_hypervisors_list(request)
            return_resource = False
            for facility in facility_list:
                instance_name = facility.hypervisor_hostname
                if instance_name == para[0]:
                    resource_para = server_resource(facility)
                    if len(resource_para) > 0 :
                        return_resource = True
                        break
                else:
                    continue
            return return_resource
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Can not get hypervisors list , error is %s' % e)

        return False

    class Meta:
        title = 'The resources of the server(%s) will be shortage(%s), handle please'
        parameters = 'The resources of the server(%s) will be shortage(%s), handle please'
        content = 'The resources of the server(%s) will be shortage(%s), handle please'
        work_func = 'get_service_resource_info'
        category = 'instance_resource'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateServerResourceShortagePrepare, self).__init__(uuid, role,
                                                                  tenant_id,
                                                                  prepare_id,
                                                                  *arg)

from dashboard.log_manage.models import LoggingAction

class CreateLogItemToLargePrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'The number of the logs item is so large(%s), handle please',
        'content': '',
        'work_func': '',
        'category': 'log_manage',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """

    def update_status(self, request, tenant_id ,parameters):
        try:
            log_lists = LoggingAction.objects.order_by('-create_at').all()
            logs = len(log_lists)
            if logs <= 900:
                return True
            return False
        except Exception, exc:
            LOG.info('Error is : %s' % exc)
            return False

    def prepare_list(self, request, prepare_id):
        pass

    class Meta:
        title = 'The number of the logs item is so large(%s), handle please'
        parameters = 'The number of the logs item is so large(%s), handle please'
        content = 'The number of the logs item is so large(%s), handle please'
        work_func = 'log_large_page'
        category = 'log_manage'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'


    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateLogItemToLargePrepare, self).__init__(uuid, role, tenant_id,
                                                          prepare_id, *arg)


class CreateFindSystemISOFilePrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'There is a system ISO file(%s), handle please',
        'content': '',
        'work_func': '',
        'category': 'software_manage',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """

    def update_status(self, request, tenant_id ,parameters):
        pass

    def prepare_list(self, request, prepare_id):
        pass

    class Meta:
        title = 'There is a system ISO file(%s), handle please'
        parameters = 'There is a system ISO file(%s), handle please'
        content = 'There is a system ISO file(%s), handle please'
        work_func = 'soft_wares_upload_success'
        category = 'software_manage'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateFindSystemISOFilePrepare, self).__init__(uuid, role,
                                                             tenant_id,
                                                             prepare_id, *arg)

#
class CreateInstancePrepare(BasePrepare):
    """
     'TYPE_SECOND_CREATE_TENANT': {
        'title': 'Please create your first instance',
        'content': '',
        'work_func': '',
        'category': 'instance_manage',
        'role' = 'ROLE_ADMIN',
        'tenant_id' = ''},
    """

    def update_status(self, request, tenant_id ,parameters):
        search_ins = []
        role = get_user_role_name(request)
        try:
            project_admin_tenants = api.keystone.tenant_list(request,
                                                             admin=True)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('The method get_instance_data raise exception: %s' % e)
            return False

        if role == ROLE_PROJECTADMIN:
            for pro_admin_tenant in project_admin_tenants:
                search_ins.append(pro_admin_tenant.id)

        instances = []
        try:
            instances = api.nova.server_list(request, all_tenants=True)
            if len(search_ins) != 0:
                instances = [inst for inst in instances if
                             inst.tenant_id in search_ins]
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve instance list. %s' % e)

        if len(instances) > 0:
            return True
        return False

    def prepare_list(self, request, prepare_id):
        pass

    class Meta:
        title = 'Please create your first instance'
        parameters = 'Please create your first instance'
        content = 'Please create your first instance'
        work_func = 'start_image_launch_instance'
        category = 'image_template_manage'
        role = ROLE_ADMIN
        tenant_id = 'admin'
        prepare_id = 'base'

    def __init__(self, uuid=None, role=None, tenant_id=None, prepare_id=None,
                 *arg):
        super(CreateInstancePrepare, self).__init__(uuid, role, tenant_id,
                                                    prepare_id, *arg)


def usages_attribute(usages_attr):
    used = usages_attr['used']
    quota = usages_attr['quota']
    if used != 0 and used / (quota*1.0) < 0.5:
        return True
    return False


"""Unit Test Code Here"""
if __name__ == '__main__':
    prepare = CreateTenantPrepare(None, 'sdfwe')


def server_resource(facility):
#    instance_name = facility.hypervisor_hostname
    server_str = ''
    memory_mb = facility.memory_mb * 1.5
    memory_mb_used = facility.memory_mb_used
    local_gb_used = facility.local_gb_used
    local_gb = facility.local_gb
    memory_mb_per = int((memory_mb_used * 100) / memory_mb)
    local_gb_per = int((local_gb_used * 100) / local_gb)
    instance_online = getattr(facility, 'num_vm_active', 0)
    num_instances = getattr(facility, 'num_instances', 0)
    cpu_use = facility.cpu_usage
    if cpu_use < 10:
        server_str += 'CPU'

    if memory_mb_per < 10:
        if len(server_str) > 0:
            server_str += ',Memory'
        else:
            server_str += 'Memory'
    if local_gb_per < 10:
        if len(server_str) > 0:
            server_str += ',Disk'
        else:
            server_str += 'Disk'

    return server_str

