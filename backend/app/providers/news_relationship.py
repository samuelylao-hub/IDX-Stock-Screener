from dataclasses import dataclass


SOURCE_ROLE_PRIMARY = "PRIMARY"
SOURCE_ROLE_OFFICIAL = "OFFICIAL"
SOURCE_ROLE_INDEPENDENT = "INDEPENDENT"
SOURCE_ROLE_SECONDARY = "SECONDARY"
SOURCE_ROLE_UNVERIFIED = "UNVERIFIED"


@dataclass
class SourceRelationship:
    source_name: str
    source_role: str
    derived_from: str | None = None
    relationship_note: str | None = None


def create_source_relationship(
    source_name: str,
    source_type: str,
    is_primary: bool = False,
    derived_from: str | None = None,
) -> SourceRelationship:

    if source_type in {
        "REGULATOR",
        "COMPANY",
    }:
        role = SOURCE_ROLE_OFFICIAL

    elif is_primary:
        role = SOURCE_ROLE_PRIMARY

    elif source_type in {
        "GLOBAL_MEDIA",
        "INDONESIA_MEDIA",
    }:
        if derived_from:
            role = SOURCE_ROLE_SECONDARY
        else:
            role = SOURCE_ROLE_INDEPENDENT

    else:
        role = SOURCE_ROLE_UNVERIFIED

    if derived_from:
        note = f"Berita diturunkan dari sumber {derived_from}."
    else:
        note = None

    return SourceRelationship(
        source_name=source_name,
        source_role=role,
        derived_from=derived_from,
        relationship_note=note,
    )


def apply_source_relationship(
    source,
    relationship: SourceRelationship,
):
    source.source_role = relationship.source_role
    source.derived_from = relationship.derived_from
    source.relationship_note = relationship.relationship_note

    return source