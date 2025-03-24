import logging

from django.utils.dateparse import parse_date
from django.utils.timezone import now
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Refbook, RefbookVersion
from .serializers import RefbookSerializer, RefbookItemSerializer

logger = logging.getLogger(__name__)


class RefbookListView(generics.ListAPIView):
    """
    View for retrieving a list of reference books.

    Supports filtering by date to get reference books with versions effective on or before the specified date.
    """
    serializer_class = RefbookSerializer

    def get_queryset(self):
        """
        Returns a queryset of reference books, filtered by date if provided.

        Returns:
            QuerySet: List of reference books, filtered by date (if specified).
        """
        queryset = Refbook.objects.all()
        date_param = self.request.query_params.get('date')

        if date_param:
            parsed_date = parse_date(date_param)
            if parsed_date:
                queryset = queryset.filter(versions__start_date__lte=parsed_date).distinct()

        return queryset

    @swagger_auto_schema(
        operation_summary="Get list of refbooks",
        manual_parameters=[
            openapi.Parameter(
                name='date',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Filter refbooks by versions starting on or before this date (format: YYYY-MM-DD).',
            ),
        ],
        responses={
            200: openapi.Response(
                description='Список справочников',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refbooks': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        )
                    }
                )
            )
        },
        operation_description="Retrieve a list of refbooks. Optionally filter by a date to get refbooks with versions starting on or before that date.",
    )
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve a list of reference books.

        Returns:
            Response: JSON response with reference book data.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        formatted_response = {
            "refbooks": serializer.data
        }
        return Response(formatted_response)


class RefbookItemMixin:
    """
    Mixin for working with reference book items.

    Provides methods to retrieve reference books and versions with 404 error handling.
    """

    def _get_refbook_or_404(self, refbook_id):
        """
        Returns a reference book by ID or raises a 404 exception if the reference book is not found.

        Args:
            refbook_id (int): ID of the reference book.

        Returns:
            Refbook: Reference book object.

        Raises:
            NotFound: If the reference book is not found.
        """
        try:
            return Refbook.objects.only('id').get(id=refbook_id)
        except Refbook.DoesNotExist:
            logger.warning(f"Refbook with ID '{refbook_id}' not found.")
            raise NotFound({"error": f"Refbook with ID '{refbook_id}' not found."})

    def _get_version_or_404(self, refbook):
        """
        Returns a reference book version or raises a 404 exception if the version is not found.

        If no version is specified, returns the latest effective version.

        Args:
            refbook (Refbook): Reference book object.

        Returns:
            RefbookVersion: Reference book version object.

        Raises:
            NotFound: If the version is not found.
        """
        version_param = self.request.query_params.get('version')
        if version_param:
            try:
                return RefbookVersion.objects.only('id').prefetch_related('items').get(refbook=refbook,
                                                                                       version=version_param)
            except RefbookVersion.DoesNotExist:
                logger.warning(f"Version '{version_param}' not found for refbook ID '{refbook.id}'.")
                raise NotFound({"error": f"Version '{version_param}' not found for the given refbook."})
        latest_version = RefbookVersion.objects.filter(
            refbook=refbook,
            start_date__lte=now().date()
        ).order_by('-start_date').prefetch_related('items').first()
        if not latest_version:
            logger.warning(f"No valid version found for refbook ID '{refbook.id}'.")
            raise NotFound({"error": f"No valid version found for the refbook ID '{refbook.id}'."})
        return latest_version


class RefbookItemListView(RefbookItemMixin, ListAPIView):
    """
    View for retrieving a list of reference book items.

    Supports filtering by reference book version.
    """
    serializer_class = RefbookItemSerializer

    def get_queryset(self):
        """
        Returns a queryset of reference book items for the specified version.

        Returns:
            QuerySet: List of reference book items.
        """
        refbook_id = self.kwargs.get('id')
        refbook = self._get_refbook_or_404(refbook_id)
        version = self._get_version_or_404(refbook)

        queryset = version.items.only('code', 'value')

        return queryset

    @swagger_auto_schema(
        operation_summary="Get a list of items for a specific refbook and version.",
        operation_description="Get a list of items for a specific refbook and version.",
        manual_parameters=[
            openapi.Parameter(
                name="version",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Optional: Specify a version of the refbook (default is the latest version).",
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="List of items for the refbook",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "elements": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "code": openapi.Schema(type=openapi.TYPE_STRING, description="Item code"),
                                    "value": openapi.Schema(type=openapi.TYPE_STRING, description="Item value"),
                                },
                            ),
                        )
                    },
                ),
            ),
            404: openapi.Response(description="Refbook or version not found"),
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve a list of reference book items.

        Returns:
            Response: JSON response with reference book item data.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        formatted_response = {
            "elements": serializer.data
        }
        return Response(formatted_response)


class RefbookItemValidationView(RefbookItemMixin, APIView):
    """
    View for validating the existence of a code-value pair in a reference book.

    Supports validation for a specified version or the latest available version.
    """

    @swagger_auto_schema(
        operation_summary="Validate if a code-value pair exists in a refbook version",
        operation_description="Checks whether a specific code and value exist in the latest or specified version of a refbook.",
        manual_parameters=[
            openapi.Parameter(
                'code',
                openapi.IN_QUERY,
                description="The code of the refbook item to validate.",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'value',
                openapi.IN_QUERY,
                description="The value of the refbook item to validate.",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'version',
                openapi.IN_QUERY,
                description="(Optional) Specify a version of the refbook to validate against. If not provided, the latest available version will be used.",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Validation result",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'valid': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Indicates whether the code-value pair is valid"
                        )
                    }
                ),
                examples={
                    "application/json": {
                        "valid": True
                    }
                }
            ),
            400: openapi.Response(
                description="Missing required parameters",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message describing missing parameters"
                        )
                    }
                ),
                examples={
                    "application/json": {"error": "Missing required parameters: code or/and value."}
                }
            ),
            404: openapi.Response(
                description="Refbook or version not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message for not finding the refbook or version"
                        )
                    }
                ),
                examples={
                    "application/json": {"error": "Refbook with ID '123' not found."}
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to validate the existence of a code-value pair in a reference book.

        Returns:
            Response: JSON response with the validation result.
        """
        refbook_id = self.kwargs.get('id')
        code = request.query_params.get('code')
        value = request.query_params.get('value')

        if not code or not value:
            logger.error(f"Validation failed: Missing required parameters (code: {code}, value: {value})")
            return Response(
                {"error": "Missing required parameters: code or/and value."},
                status=status.HTTP_400_BAD_REQUEST
            )

        refbook = self._get_refbook_or_404(refbook_id)
        version = self._get_version_or_404(refbook)

        element_exists = version.items.filter(
            code=code,
            value=value
        ).exists()

        logger.info(f"Validation {'successful' if element_exists else 'failed'} for refbook ID '{refbook_id}', "
                    f"code '{code}', value '{value}', version '{version.version}'.")

        return Response(
            {"valid": element_exists},
            status=status.HTTP_200_OK
        )
