from app.models.reference_sample import ReferenceSample
from app.services.reference_library_service import ReferenceLibraryService


def test_reference_filter_by_tag() -> None:
    service = ReferenceLibraryService()
    samples = [ReferenceSample(tags=["fill"]), ReferenceSample(tags=["style_color"])]
    assert len(service.filter_by_tag(samples, "fill")) == 1
