from django.utils.timezone import now
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import Refbook, RefbookVersion
from .serializers import RefbookItemSerializer


class RefbookItemMixin:
    def _get_refbook_or_404(self, refbook_id):
        try:
            return Refbook.objects.only('id').get(id=refbook_id)
        except Refbook.DoesNotExist:
            raise NotFound({"error": f"Refbook with ID '{refbook_id}' not found."})

    def _get_version_or_404(self, refbook):
        version_param = self.request.query_params.get('version')
        if version_param:
            try:
                version = RefbookVersion.objects.only('id').prefetch_related('items').get(refbook=refbook,
                                                                                          version=version_param)
                if not version:
                    raise NotFound({"error": f"Version '{version_param}' not found for the given refbook."})
                return version
            except RefbookVersion.DoesNotExist:
                raise NotFound({"error": f"Version '{version_param}' not found for the given refbook."})
        latest_version = RefbookVersion.objects.filter(
            refbook=refbook,
            start_date__lte=now().date()
        ).prefetch_related('items').order_by('-start_date').first()
        if not latest_version:
            raise NotFound({"error": f"No valid version found for the refbook ID '{refbook.id}'."})
        return latest_version


class RefbookItemListView(RefbookItemMixin, generics.ListAPIView):
    serializer_class = RefbookItemSerializer

    def get_queryset(self):
        refbook_id = self.kwargs.get('id')
        refbook = self._get_refbook_or_404(refbook_id)
        version = self._get_version_or_404(refbook)

        queryset = version.items.only('code', 'value')

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        formatted_response = {
            "elements": serializer.data
        }
        return Response(formatted_response)


class RefbookItemValidationView(RefbookItemMixin, generics.ListAPIView):

    def get(self, request, *args, **kwargs):
        refbook_id = self.kwargs.get('id')
        code = request.query_params.get('code')
        value = request.query_params.get('value')

        if not code or not value:
            return Response(
                {"error": "Missing required parameters: code or/and value."},
                status=status.HTTP_400_BAD_REQUEST
            )

        refbook = self._get_refbook_or_404(refbook_id)
        version = self._get_version_or_404(refbook)

        element_exists = version.items.filter(
            version=version,
            code=code,
            value=value
        ).exists()

        return Response(
            {"valid": element_exists},
            status=status.HTTP_200_OK
        )
