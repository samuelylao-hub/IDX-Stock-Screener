from backend.app.providers.news_relationship import (
    create_source_relationship,
)


def run_test(
    name,
    source_name,
    source_type,
    is_primary=False,
    derived_from=None,
):
    result = create_source_relationship(
        source_name=source_name,
        source_type=source_type,
        is_primary=is_primary,
        derived_from=derived_from,
    )

    print(
        name,
        "=>",
        result.source_role,
        "| derived_from=",
        result.derived_from,
    )


if __name__ == "__main__":
    run_test(
        "IDX",
        "IDX",
        "REGULATOR",
        is_primary=True,
    )

    run_test(
        "REUTERS",
        "Reuters",
        "GLOBAL_MEDIA",
    )

    run_test(
        "KONTAN_DERIVED",
        "Kontan",
        "INDONESIA_MEDIA",
        derived_from="Reuters",
    )

    run_test(
        "TWITTER",
        "Twitter",
        "UNKNOWN",
    )
