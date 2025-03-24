from django.db import models
from django.utils.timezone import now


class Refbook(models.Model):
    """
    Reference Book Model.

    Attributes:
        code (str): Unique code of the reference book.
        name (str): Name of the reference book.
        description (str, optional): Description of the reference book.

    Properties:
        current_version (str): Current version of the reference book.
        current_version_start_date (str): Effective start date of the current version.

    Methods:
        _get_latest_version(): Returns the latest version of the reference book.
    """
    code = models.CharField(max_length=100, unique=True, verbose_name="Код")
    name = models.CharField(max_length=300, verbose_name="Наименование")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    def __str__(self):
        return self.name

    @property
    def current_version(self):
        latest_version = self._get_latest_version()
        return latest_version.version if latest_version else 'Нет версии'

    @property
    def current_version_start_date(self):
        latest_version = self._get_latest_version()
        return latest_version.start_date if latest_version else 'Нет даты'

    def _get_latest_version(self):
        return self.versions.filter(start_date__lte=now().date()).order_by('-start_date').first()

    class Meta:
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'


class RefbookVersion(models.Model):
    """
    Reference Book Version Model.

    Attributes:
        refbook (Refbook): Associated reference book.
        version (str): Version of the reference book.
        start_date (date): Effective start date of the version.

    Meta:
        constraints: Unique constraint for the pair of refbook and version.
        ordering: Sorting by descending start date.
    """
    refbook = models.ForeignKey(Refbook, on_delete=models.CASCADE, related_name='versions',
                                verbose_name="Идентификатор справочника")
    version = models.CharField(max_length=50, verbose_name="Версия")
    start_date = models.DateField(verbose_name="Дата начала действия версии")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['refbook', 'version'], name='unique_refbook_version')
        ]
        ordering = ['-start_date']
        verbose_name = 'Версия справочника'
        verbose_name_plural = 'Версии справочников'

    def __str__(self):
        return f'{self.refbook.name} - {self.version}'


class RefbookItem(models.Model):
    """
    Reference Book Item Model.

    Attributes:
        version (RefbookVersion): Associated reference book version.
        code (str): Item code.
        value (str): Item value.

    Meta:
        constraints: Unique constraint for the pair of version and code.
    """
    version = models.ForeignKey(RefbookVersion, on_delete=models.CASCADE, related_name='items',
                                verbose_name="Идентификатор версии")
    code = models.CharField(max_length=100, verbose_name="Код элемента")
    value = models.CharField(max_length=300, verbose_name="Значение элемента")

    def __str__(self):
        return self.value

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['version', 'code'], name='unique_version_code')
        ]
        verbose_name = 'Элемент справочника'
        verbose_name_plural = 'Элементы справочников'
