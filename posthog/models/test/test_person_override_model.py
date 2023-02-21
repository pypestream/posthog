import contextlib
import datetime as dt
from uuid import uuid4

import pytest
from django.db.utils import DEFAULT_DB_ALIAS, ConnectionHandler, IntegrityError

from posthog.api.test.test_organization import create_organization
from posthog.api.test.test_team import create_team
from posthog.models import PersonOverride, Team
from posthog.models.person.person import Person

pytestmark = pytest.mark.django_db


def test_person_override_disallows_overriding_to_itself():
    """Test old_person_id cannot match override_person_id.

    This is enforced by a CHECK constraint old_person_id_different_from_override_person_id
    """
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    person_id = uuid4()

    Person.objects.create(
        team_id=team.pk,
        uuid=person_id,
    )

    with pytest.raises(IntegrityError):
        PersonOverride.objects.create(
            team=team,
            old_person_id=person_id,
            override_person_id=person_id,
            oldest_event=oldest_event,
            version=0,
        ).save()


def test_person_override_disallows_same_old_person_id():
    """Test a new old_person_id cannot match an existing old_person_id.

    This is enforced by a UNIQUE constraint on (team_id, old_person_id)
    """
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()
    new_override_person_id = uuid4()

    Person.objects.create(
        team_id=team.pk,
        uuid=override_person_id,
    )

    person_override = PersonOverride.objects.create(
        team=team,
        old_person_id=old_person_id,
        override_person_id=override_person_id,
        oldest_event=oldest_event,
        version=1,
    )
    person_override.save()

    assert person_override.old_person_id == old_person_id
    assert person_override.override_person_id == override_person_id

    Person.objects.create(
        team_id=team.pk,
        uuid=new_override_person_id,
    )

    with pytest.raises(IntegrityError):
        PersonOverride.objects.create(
            team=team,
            old_person_id=old_person_id,
            override_person_id=new_override_person_id,
            oldest_event=oldest_event,
            version=1,
        ).save()


def test_person_override_same_old_person_id_in_different_teams():
    """Test a new old_person_id can match an existing from a different team."""
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()
    new_team = Team.objects.create(
        organization=organization,
        api_token="a different token",
    )

    Person.objects.create(
        team_id=team.pk,
        uuid=override_person_id,
    )

    p1 = PersonOverride.objects.create(
        team=team,
        old_person_id=old_person_id,
        override_person_id=override_person_id,
        oldest_event=oldest_event,
        version=1,
    )
    p1.save()

    assert p1.old_person_id == old_person_id
    assert p1.override_person_id == override_person_id

    p2 = PersonOverride.objects.create(
        team=new_team,
        old_person_id=old_person_id,
        override_person_id=override_person_id,
        oldest_event=oldest_event,
        version=1,
    )
    p2.save()

    assert p1.old_person_id == p2.old_person_id
    assert p1.override_person_id == p2.override_person_id
    assert p1.team != p2.team


def test_person_override_allows_override_person_id_as_old_person_id_in_different_teams():
    """Test a new old_person_id can match an override in a different team."""
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()
    new_override_person_id = uuid4()
    new_team = Team.objects.create(
        organization=organization,
        api_token="a much different token",
    )

    Person.objects.create(
        team_id=team.pk,
        uuid=override_person_id,
    )

    p1 = PersonOverride.objects.create(
        team=team,
        old_person_id=old_person_id,
        override_person_id=override_person_id,
        oldest_event=oldest_event,
        version=1,
    )
    p1.save()

    assert p1.old_person_id == old_person_id
    assert p1.override_person_id == override_person_id

    Person.objects.create(
        team_id=team.pk,
        uuid=new_override_person_id,
    )

    p2 = PersonOverride.objects.create(
        team=new_team,
        old_person_id=override_person_id,
        override_person_id=new_override_person_id,
        oldest_event=oldest_event,
        version=1,
    )
    p2.save()

    assert p1.override_person_id == p2.old_person_id
    assert p2.override_person_id == new_override_person_id
    assert p1.team != p2.team


def test_person_override_must_exist_in_person_table():
    """This is guaranteed by the foreign key constraint."""
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    person_id = uuid4()

    Person.objects.create(
        team_id=team.pk,
        uuid=person_id,
    )

    with pytest.raises(IntegrityError):
        PersonOverride.objects.create(
            team=team,
            old_person_id=person_id,
            override_person_id=person_id,
            oldest_event=oldest_event,
            version=0,
        ).save()


def test_person_override_allows_duplicate_override_person_id():
    """Test duplicate override_person_ids with different old_person_ids are allowed."""
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    override_person_id = uuid4()
    n_person_overrides = 2
    created = []

    Person.objects.create(uuid=override_person_id, team=team)

    for _ in range(n_person_overrides):
        old_person_id = uuid4()

        person_override = PersonOverride.objects.create(
            team=team,
            old_person_id=old_person_id,
            override_person_id=override_person_id,
            oldest_event=oldest_event,
            version=1,
        )
        person_override.save()

        created.append(person_override)

    assert all(p.override_person_id == override_person_id for p in created)
    assert len(set(p.old_person_id for p in created)) == n_person_overrides


def test_person_override_old_person_id_as_override_person_id_in_different_teams():
    """Test a new override_person_id can match an old in a different team."""
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()
    new_old_person_id = uuid4()
    new_team = Team.objects.create(
        organization=organization,
        api_token="a significantly different token",
    )

    Person.objects.create(uuid=old_person_id, team=team)
    Person.objects.create(uuid=override_person_id, team=team)
    Person.objects.create(uuid=new_old_person_id, team=team)

    p1 = PersonOverride.objects.create(
        team=team,
        old_person_id=old_person_id,
        override_person_id=override_person_id,
        oldest_event=oldest_event,
        version=1,
    )
    p1.save()

    assert p1.old_person_id == old_person_id
    assert p1.override_person_id == override_person_id

    p2 = PersonOverride.objects.create(
        team=new_team,
        old_person_id=new_old_person_id,
        override_person_id=old_person_id,
        oldest_event=oldest_event,
        version=1,
    )
    p2.save()

    assert p1.old_person_id == p2.override_person_id
    assert p2.old_person_id == new_old_person_id
    assert p1.team != p2.team


@pytest.mark.django_db(transaction=True)
def test_person_deletion_disallowed_when_override_exists():
    """Person deletion would result in an error if the override exists
    TODO: fix all person deletions
    """
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()

    override_person = Person.objects.create(
        team_id=team.pk,
        uuid=override_person_id,
    )
    PersonOverride.objects.create(
        team=team,
        old_person_id=old_person_id,
        override_person_id=override_person_id,
        oldest_event=oldest_event,
        version=0,
    ).save()

    with pytest.raises(IntegrityError):
        override_person.delete()


"""
Concurrency tests:
- there are two cases that we want to check for
    - concurrent merges
    - concurrent merge and person deletion

In both cases one of the transactions will wait on the lock,
so they can only complete in one order (the second one failing).
TODO: Tomas to update the comment

Tests:
concurrency between:
- 2 merges
    - the later started transaction finishes first
- merge & real person delete (with deletes overrides)
    - merge starts - person deletion runs fully - merge finishes
    - person d starts - merge finishes fully - person d finishes
"""


@pytest.mark.django_db(transaction=True)
def test_concurrent_delete_first_then_merge_fails():
    # Can't do concurrently the other order due to waiting on the lock forever
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()

    Person.objects.create(uuid=old_person_id, team=team)
    Person.objects.create(uuid=override_person_id, team=team)
    with create_connection() as merge_cursor, create_connection() as delete_cursor:
        # each transaction gets a "copy" of the DB state
        merge_cursor.execute("BEGIN")
        delete_cursor.execute("BEGIN")
        # merge and delete
        _merge_people(team, merge_cursor, old_person_id, override_person_id, oldest_event)
        _delete_person(team, delete_cursor, override_person_id)

        # finish delete first, then merge fails
        delete_cursor.execute("COMMIT")
        with pytest.raises(IntegrityError):
            merge_cursor.execute("COMMIT")

        # TODO: make sure plugin server handles this properly


@pytest.mark.django_db(transaction=True)
def test_merge_first_then_delete():
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()

    Person.objects.create(uuid=old_person_id, team=team)
    Person.objects.create(uuid=override_person_id, team=team)
    with create_connection() as merge_cursor, create_connection() as delete_cursor:
        # each transaction gets a "copy" of the DB state
        merge_cursor.execute("BEGIN")
        # merge and delete
        _merge_people(team, merge_cursor, old_person_id, override_person_id, oldest_event)
        # finish merge first
        merge_cursor.execute("COMMIT")

        delete_cursor.execute("BEGIN")
        _delete_person(team, delete_cursor, override_person_id)
        delete_cursor.execute("COMMIT")

        # Note: in plugin-server we don't need to retry deletes because merge would wait on the delete
        # person lock. or should we retry person deletions?


@pytest.mark.django_db(transaction=True)
def test_2_concequitive_merges():
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()
    new_override_person_id = uuid4()

    Person.objects.create(uuid=old_person_id, team=team)
    Person.objects.create(uuid=override_person_id, team=team)
    Person.objects.create(uuid=new_override_person_id, team=team)

    with create_connection() as first_cursor, create_connection() as second_cursor:
        # each transaction gets a "copy" of the DB state
        first_cursor.execute("BEGIN")
        _merge_people(team, first_cursor, old_person_id, override_person_id, oldest_event)
        first_cursor.execute("COMMIT")
        second_cursor.execute("BEGIN")
        # try to do the merges
        _merge_people(team, second_cursor, override_person_id, new_override_person_id, oldest_event)

        # the one finishing first succeeds, the one finishing second fails
        second_cursor.execute("COMMIT")


@pytest.mark.django_db(transaction=True)
def test_person_override_disallows_old_person_id_as_override_person_id_race_conditions():
    """Test a new override_person_id cannot match an existing old_person_id.

    Under the assumption: an entry to overrides table is added only in a transaction
    that also deletes the old person.
    We want to guarantee that the same person id can't exist both as old and override id.

    We re-use the old_person_id from the first model created as the override_person_id
    of the second model. We expect an exception on saving this second model.

    Note that to test the race condition scenario we need to:

     1. create multiple concurrent transactions, such that we can verify
        constraints are enforced at COMMIT time.
     2. enable transactions for the Django test. This is more so we can see data
        from the main Django PostgreSQL connection session in the other
        concurrent transactions. Not 100% required but makes things a little
        easier to write.
    """
    organization = create_organization(name="test")
    team = create_team(organization=organization)

    oldest_event = dt.datetime.now(dt.timezone.utc)
    old_person_id = uuid4()
    override_person_id = uuid4()
    new_override_person_id = uuid4()

    Person.objects.create(uuid=old_person_id, team=team)
    Person.objects.create(uuid=override_person_id, team=team)
    Person.objects.create(uuid=new_override_person_id, team=team)

    with create_connection() as first_cursor, create_connection() as second_cursor:
        # each transaction gets a "copy" of the DB state
        first_cursor.execute("BEGIN")
        second_cursor.execute("BEGIN")

        # try to do the merges
        _merge_people(team, first_cursor, old_person_id, override_person_id, oldest_event)
        _merge_people(team, second_cursor, override_person_id, new_override_person_id, oldest_event)

        # the one finishing first succeeds, the one finishing second fails
        second_cursor.execute("COMMIT")
        with pytest.raises(IntegrityError):
            first_cursor.execute("COMMIT")

        assert list(PersonOverride.objects.all().values_list("old_person_id", "override_person_id")) == [
            (override_person_id, new_override_person_id),
        ]  # type: ignore

        # We got an IntegrityError, so the first transaction was rolled back. We'll
        # need to try this transaction again to get to the state we expect.
        first_cursor.execute("BEGIN")
        _merge_people(team, first_cursor, old_person_id, override_person_id, oldest_event)
        first_cursor.execute("COMMIT")

        mappings = list(PersonOverride.objects.all().values_list("old_person_id", "override_person_id"))

        assert sorted(mappings) == sorted(
            [
                (override_person_id, new_override_person_id),
                (old_person_id, new_override_person_id),
            ]
        ), f"{mappings=} {old_person_id=}, {override_person_id=}, {new_override_person_id=}"  # type: ignore


@contextlib.contextmanager
def create_connection(alias=DEFAULT_DB_ALIAS):
    connection = ConnectionHandler().create_connection(alias)  # type: ignore
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET lock_timeout TO '10s'")
            try:
                yield cursor
            finally:
                # Make sure that it there was a transaction still open, then roll it
                # back.
                cursor.execute("ROLLBACK")
                cursor.close()

    finally:
        connection.close()


def _merge_people(team, cursor, old_person_id, override_person_id, oldest_event):
    """
    Merge two people together, using the override_person_id as the canonical
    person.

    This mimics how we expect the code to do person merges, i.e. in a transaction
    that deletes the old person, adds old person->override person override and updates
    all old person as override person rows to now point to the new override person.

    This function is meant to be run in a separate thread, so that we can test
    that the transaction is rolled back if there is a conflict.

    Of note is that we handle cases where the override_person_id is already
    merged into another person, meaning we need to first resolve that
    override_person_id to the one it was merged in to.

    Note that we don't actually handle the merge on the posthog_person table,
    but rather simply DELETE the record associated with `old_person_id`. It may
    be that we remove the implmentation of deleting merged persons, in which
    case we'll need to update the constraint to also include e.g. the
    `is_deleted` flag we may add.
    """
    cursor.execute(
        """
            SELECT
                override_person_id
            FROM
                posthog_personoverride
            WHERE
                old_person_id = %(override_person_id)s
                AND team_id = %(team_id)s
        """,
        {"team_id": team.id, "override_person_id": override_person_id},
    )

    resolve_override_person_id = cursor.fetchone() or override_person_id

    cursor.execute(
        """
            DELETE FROM
                posthog_person
            WHERE
                uuid = %(old_person_id)s
                AND team_id = %(team_id)s;

            INSERT INTO posthog_personoverride(
                team_id,
                old_person_id,
                override_person_id,
                oldest_event,
                version
            )
            VALUES (
                %(team_id)s,
                %(old_person_id)s,
                %(override_person_id)s,
                %(oldest_event)s,
                1
            );

            UPDATE
                posthog_personoverride
            SET
                override_person_id = %(override_person_id)s,
                version = version + 1
            WHERE override_person_id = %(old_person_id)s
                  AND team_id = %(team_id)s;
        """,
        {
            "team_id": team.id,
            "old_person_id": old_person_id,
            "override_person_id": resolve_override_person_id,
            "oldest_event": oldest_event,
        },
    )


def _delete_person(team, cursor, person_id):
    """
    Delete the person.

    This mimics how we expect the code to do person deletions, i.e. in a transaction
    that deletes the person_overrides in addition to deleting from the person table.

    It may be that we change to using soft deletes in the person table instead in that
    case we'll need to update the constraint to also include e.g. the
    `is_deleted` flag we may add.
    """
    cursor.execute(
        """
            DELETE FROM
                posthog_personoverride
            WHERE
                override_person_id = %(person_id)s
                AND team_id = %(team_id)s;

            DELETE FROM
                posthog_person
            WHERE
                uuid = %(person_id)s
                AND team_id = %(team_id)s;
        """,
        {
            "team_id": team.id,
            "person_id": person_id,
        },
    )
