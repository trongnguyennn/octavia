#    Copyright 2018 Rackspace, US Inc.
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

from octavia_lib.api.drivers import exceptions as lib_exceptions
from oslo_config import cfg
from oslo_log import log as logging
from pecan import expose as pecan_expose
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia.api.drivers import driver_factory
from octavia.api.v2.controllers import base
from octavia.api.v2.types import provider as provider_types
from octavia.common import constants
from octavia.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ProviderController(base.BaseController):
    RBAC_TYPE = constants.RBAC_PROVIDER

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(provider_types.ProvidersRootResponse, [wtypes.text],
                         ignore_extra_args=True)
    def get_all(self, fields=None):
        """List enabled provider drivers and their descriptions."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')

        self._auth_validate_action(context, context.project_id,
                                   constants.RBAC_GET_ALL)

        enabled_providers = CONF.api_settings.enabled_provider_drivers
        response_list = [
            provider_types.ProviderResponse(name=key, description=value) for
            key, value in enabled_providers.items()]
        if fields is not None:
            response_list = self._filter_fields(response_list, fields)
        return provider_types.ProvidersRootResponse(providers=response_list)

    @pecan_expose()
    def _lookup(self, provider, *remainder):
        """Overridden pecan _lookup method for custom routing.

        Currently it checks if this was a flavor capabilities request and
        routes the request to the FlavorCapabilitiesController.
        """
        if provider and remainder:
            if remainder[0] == 'flavor_capabilities':
                return (FlavorCapabilitiesController(provider=provider),
                        remainder[1:])
            if remainder[0] == 'availability_zone_capabilities':
                return (
                    AvailabilityZoneCapabilitiesController(provider=provider),
                    remainder[1:])
        return None


class FlavorCapabilitiesController(base.BaseController):
    RBAC_TYPE = constants.RBAC_PROVIDER_FLAVOR

    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    @wsme_pecan.wsexpose(provider_types.FlavorCapabilitiesResponse,
                         [wtypes.text], ignore_extra_args=True,
                         status_code=200)
    def get_all(self, fields=None):
        context = pecan_request.context.get('octavia_context')
        self._auth_validate_action(context, context.project_id,
                                   constants.RBAC_GET_ALL)
        self.driver = driver_factory.get_driver(self.provider)
        try:
            metadata_dict = self.driver.get_supported_flavor_metadata()
        except lib_exceptions.NotImplementedError as e:
            LOG.warning('Provider %s get_supported_flavor_metadata() '
                        'reported: %s', self.provider, e.operator_fault_string)
            raise exceptions.ProviderNotImplementedError(
                prov=self.provider, user_msg=e.user_fault_string)

        # Apply any valid filters provided as URL parameters
        name_filter = None
        description_filter = None
        pagination_helper = pecan_request.context.get(
            constants.PAGINATION_HELPER)
        if pagination_helper:
            name_filter = pagination_helper.params.get(constants.NAME)
            description_filter = pagination_helper.params.get(
                constants.DESCRIPTION)
        if name_filter:
            metadata_dict = {
                key: value for key, value in metadata_dict.items() if
                key == name_filter}
        if description_filter:
            metadata_dict = {
                key: value for key, value in metadata_dict.items() if
                value == description_filter}

        response_list = [
            provider_types.ProviderResponse(name=key, description=value) for
            key, value in metadata_dict.items()]
        if fields is not None:
            response_list = self._filter_fields(response_list, fields)
        return provider_types.FlavorCapabilitiesResponse(
            flavor_capabilities=response_list)


class AvailabilityZoneCapabilitiesController(base.BaseController):
    RBAC_TYPE = constants.RBAC_PROVIDER_AVAILABILITY_ZONE

    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    @wsme_pecan.wsexpose(provider_types.AvailabilityZoneCapabilitiesResponse,
                         [wtypes.text], ignore_extra_args=True,
                         status_code=200)
    def get_all(self, fields=None):
        context = pecan_request.context.get('octavia_context')
        self._auth_validate_action(context, context.project_id,
                                   constants.RBAC_GET_ALL)
        self.driver = driver_factory.get_driver(self.provider)
        try:
            metadata_dict = (
                self.driver.get_supported_availability_zone_metadata())
        except lib_exceptions.NotImplementedError as e:
            LOG.warning(
                'Provider %s get_supported_availability_zone_metadata() '
                'reported: %s', self.provider, e.operator_fault_string)
            raise exceptions.ProviderNotImplementedError(
                prov=self.provider, user_msg=e.user_fault_string)

        # Apply any valid filters provided as URL parameters
        name_filter = None
        description_filter = None
        pagination_helper = pecan_request.context.get(
            constants.PAGINATION_HELPER)
        if pagination_helper:
            name_filter = pagination_helper.params.get(constants.NAME)
            description_filter = pagination_helper.params.get(
                constants.DESCRIPTION)
        if name_filter:
            metadata_dict = {
                key: value for key, value in metadata_dict.items() if
                key == name_filter}
        if description_filter:
            metadata_dict = {
                key: value for key, value in metadata_dict.items() if
                value == description_filter}

        response_list = [
            provider_types.ProviderResponse(name=key, description=value) for
            key, value in metadata_dict.items()]
        if fields is not None:
            response_list = self._filter_fields(response_list, fields)
        return provider_types.AvailabilityZoneCapabilitiesResponse(
            availability_zone_capabilities=response_list)
