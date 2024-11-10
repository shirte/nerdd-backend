import asyncio
import hashlib
import json

from rethinkdb import RethinkDB
from rethinkdb.errors import ReqlOpFailedError

from ..settings import RETHINKDB_DB, RETHINKDB_HOST, RETHINKDB_PORT

__all__ = ["RethinkDbRepository"]


def hash_object(obj):
    obj_str = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(obj_str.encode("utf-8")).hexdigest()


class RethinkDbRepository:
    def __init__(self):
        self.r = RethinkDB()
        self.r.set_loop_type("asyncio")

    #
    # INITIALIZATION
    #
    async def initialize(self):
        self.connection = await self.r.connect(RETHINKDB_HOST, RETHINKDB_PORT)

        # create database
        try:
            await self.r.db_create(RETHINKDB_DB).run(self.connection)
        except ReqlOpFailedError:
            pass

        # create tables
        await self.create_module_table()
        await self.create_sources_table()
        await self.create_jobs_table()
        await self.create_results_table()

    #
    # MODULES
    #
    async def get_module_changes(self):
        return (
            await self.r.db(RETHINKDB_DB)
            .table("modules")
            .changes(include_initial=True)
            .run(self.connection)
        )

    async def get_all_modules(self):
        cursor = await self.r.db(RETHINKDB_DB).table("modules").run(self.connection)
        return [item async for item in cursor]

    async def get_module_by_id(self, id):
        return (
            await self.r.db(RETHINKDB_DB).table("modules").get(id).run(self.connection)
        )

    async def create_module_table(self):
        try:
            await self.r.db(RETHINKDB_DB).table_create("modules").run(self.connection)
        except ReqlOpFailedError:
            pass

    async def get_most_recent_version(self, module_id):
        # TODO: incorporate versioning
        return (
            await self.r.db(RETHINKDB_DB)
            .table("modules")
            .get(module_id)
            .run(self.connection)
        )

    async def upsert_module(self, module):
        # TODO: incorporate versioning
        # compute the primary key from name and version
        # if "version" in module.keys():
        #     version = module["version"]
        # else:
        #     version = "1.0.0"
        # name = module["name"]
        module["id"] = module["name"]

        # insert the module (or update if it matches an existing name-version combo)
        await (
            self.r.db(RETHINKDB_DB)
            .table("modules")
            .insert(module, conflict="update")
            .run(self.connection)
        )

    #
    # JOBS
    #
    async def create_jobs_table(self):
        try:
            await (
                self.r.db(RETHINKDB_DB)
                .table_create("jobs", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def upsert_job(self, job):
        await (
            self.r.db(RETHINKDB_DB)
            .table("jobs")
            .insert(job, conflict="update")
            .run(self.connection)
        )

    async def get_job_by_id(self, id):
        return await self.r.db(RETHINKDB_DB).table("jobs").get(id).run(self.connection)

    async def delete_job_by_id(self, id):
        await (
            self.r.db(RETHINKDB_DB).table("jobs").get(id).delete().run(self.connection)
        )

    #
    # SOURCES
    #
    async def create_sources_table(self):
        try:
            await (
                self.r.db(RETHINKDB_DB)
                .table_create("sources", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def upsert_source(self, source):
        await (
            self.r.db(RETHINKDB_DB)
            .table("sources")
            .insert(source, conflict="update")
            .run(self.connection)
        )

    async def get_source_by_id(self, id):
        return (
            await self.r.db(RETHINKDB_DB).table("sources").get(id).run(self.connection)
        )

    async def delete_source_by_id(self, id):
        await (
            self.r.db(RETHINKDB_DB)
            .table("sources")
            .get(id)
            .delete()
            .run(self.connection)
        )

    #
    # RESULTS
    #
    async def create_results_table(self):
        try:
            await (
                self.r.db(RETHINKDB_DB)
                .table_create("results", primary_key="id")
                .run(self.connection)
            )
        except ReqlOpFailedError:
            pass

    async def get_all_results_by_job_id(self, job_id):
        return (
            await self.r.db(RETHINKDB_DB)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .run(self.connection)
        )

    async def get_num_processed_entries_by_job_id(self, job_id):
        return (
            await self.r.db(RETHINKDB_DB)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .pluck("mol_id")
            .distinct()
            .count()
            .run(self.connection)
        )

    async def get_results_by_job_id(self, job_id, start_mol_id, end_mol_id):
        return (
            await self.r.db(RETHINKDB_DB)
            .table("results")
            .filter(
                (self.r.row["job_id"] == job_id)
                & (self.r.row["mol_id"] >= start_mol_id)
                & (self.r.row["mol_id"] <= end_mol_id)
            )
            .order_by("mol_id")
            .run(self.connection)
        )

    async def upsert_result(self, result):
        await (
            self.r.db(RETHINKDB_DB)
            .table("results")
            .insert(result, conflict="update")
            .run(self.connection)
        )

    async def get_job_changes(self, job_id):
        return (
            await self.r.db(RETHINKDB_DB)
            .table("results")
            .filter(self.r.row["job_id"] == job_id)
            .pluck("mol_id")
            .changes(include_initial=False)
            .run(self.connection)
        )

    async def get_result_changes(self, job_id, start_mol_id, end_mol_id):
        return (
            await self.r.db(RETHINKDB_DB)
            .table("results")
            .filter(
                (self.r.row["job_id"] == job_id)
                & (self.r.row["mol_id"] >= start_mol_id)
                & (self.r.row["mol_id"] <= end_mol_id)
            )
            .changes(include_initial=False)
            .run(self.connection)
        )
