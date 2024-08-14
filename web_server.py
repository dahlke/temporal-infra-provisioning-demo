from pdb import run
import uuid
import os

from dataclasses import dataclass, field
from typing import Dict
from flask import Flask, render_template, request, jsonify
from shared import get_temporal_client, TerraformRunDetails
from workflows import ProvisionInfraWorkflow
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

app = Flask(__name__)

provision_status_key = SearchAttributeKey.for_text("provisionStatus")
tf_directory_key = SearchAttributeKey.for_text("tfDirectory")
scenarios = [
	"HappyPath",
	"AdvancedVisibility",
	"HumanInLoopSignal",
	# TODO
	# "HumanInLoopUpdate",
	# "ChildWorkflow",
	"APIFailure",
	"RecoverableFailure",
	"NonRecoverableFailure",
]
tf_runs = []
tf_modules = [
	{
		"name": "temporal_cloud",
		"description": "This deploys the Temporal Cloud infrastructure.",
		"directory": "./terraform/tcloud"
	},
	{
		"name": "something_local",
		"description": "This deploys something locally to my machine.",
		"directory": "./terraform"
	}
]


@app.route("/", methods=["GET", "POST"])
async def main():
	# TODO
	tf_run_id = f"provision-infra-{uuid.uuid4()}"
	return render_template(
		"index.html",
		tf_modules=tf_modules,
		tf_run_id=tf_run_id,
		scenarios=scenarios
	)

@app.route("/provision_infra", methods=["GET", "POST"])
async def provision_infra():
	selected_scenario = request.args.get('scenario')
	tf_run_id = request.args.get('tf_run_id', "")
	tf_module_name = request.args.get('tf_module_name')
	tcloud_env_vars = { "TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY }
	tcloud_tf_dir = ""

	for module in tf_modules:
		if module["name"] == tf_module_name:
			tcloud_tf_dir = module["directory"]
			break

	tf_run_details = TerraformRunDetails(
		id=tf_run_id,
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars
	)
	print(tf_run_details)

	# TODO: add a run to the table

	client = await get_temporal_client()

	handle = await client.start_workflow(
		ProvisionInfraWorkflow.run,
		tf_run_details,
		id=tf_run_id,
		task_queue=TEMPORAL_TASK_QUEUE,
		search_attributes=TypedSearchAttributes([
			SearchAttributePair(provision_status_key, "uninitialized"),
			SearchAttributePair(tf_directory_key, tcloud_tf_dir)
		]),
	)

	# result = await handle.result()

	return render_template(
		"index.html",
		tf_modules=tf_modules,
		tf_run_id=tf_run_id,
		scenarios=scenarios
	)

if __name__ == "__main__":
	app.run(debug=True, port=3000)
