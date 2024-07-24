import os
import sys
import traceback

import openai
import pytest
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(
    0, os.path.abspath("../..")
)  # Adds the parent directory to the system path
from unittest.mock import MagicMock, patch

import litellm
from litellm import completion, completion_cost, embedding

litellm.set_verbose = False


def test_openai_embedding():
    try:
        litellm.set_verbose = True
        response = embedding(
            model="text-embedding-ada-002",
            input=["good morning from litellm", "this is another item"],
            metadata={"anything": "good day"},
        )
        litellm_response = dict(response)
        litellm_response_keys = set(litellm_response.keys())
        litellm_response_keys.discard("_response_ms")

        print(litellm_response_keys)
        print("LiteLLM Response\n")
        # print(litellm_response)

        # same request with OpenAI 1.0+
        import openai

        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=["good morning from litellm", "this is another item"],
        )

        response = dict(response)
        openai_response_keys = set(response.keys())
        print(openai_response_keys)
        assert (
            litellm_response_keys == openai_response_keys
        )  # ENSURE the Keys in litellm response is exactly what the openai package returns
        assert (
            len(litellm_response["data"]) == 2
        )  # expect two embedding responses from litellm_response since input had two
        print(openai_response_keys)
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_openai_embedding()


def test_openai_embedding_3():
    try:
        litellm.set_verbose = True
        response = embedding(
            model="text-embedding-3-small",
            input=["good morning from litellm", "this is another item"],
            metadata={"anything": "good day"},
            dimensions=5,
        )
        print(f"response:", response)
        litellm_response = dict(response)
        litellm_response_keys = set(litellm_response.keys())
        litellm_response_keys.discard("_response_ms")

        print(litellm_response_keys)
        print("LiteLLM Response\n")
        # print(litellm_response)

        # same request with OpenAI 1.0+
        import openai

        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=["good morning from litellm", "this is another item"],
            dimensions=5,
        )

        response = dict(response)
        openai_response_keys = set(response.keys())
        print(openai_response_keys)
        assert (
            litellm_response_keys == openai_response_keys
        )  # ENSURE the Keys in litellm response is exactly what the openai package returns
        assert (
            len(litellm_response["data"]) == 2
        )  # expect two embedding responses from litellm_response since input had two
        print(openai_response_keys)
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


def test_openai_azure_embedding_simple():
    try:
        litellm.set_verbose = True
        response = embedding(
            model="azure/azure-embedding-model",
            input=["good morning from litellm"],
        )
        print(response)
        response_keys = set(dict(response).keys())
        response_keys.discard("_response_ms")
        assert set(["usage", "model", "object", "data"]) == set(
            response_keys
        )  # assert litellm response has expected keys from OpenAI embedding response

        request_cost = litellm.completion_cost(completion_response=response)

        print("Calculated request cost=", request_cost)

        assert isinstance(response.usage, litellm.Usage)

    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_openai_azure_embedding_simple()


def test_openai_azure_embedding_timeouts():
    try:
        response = embedding(
            model="azure/azure-embedding-model",
            input=["good morning from litellm"],
            timeout=0.00001,
        )
        print(response)
    except openai.APITimeoutError:
        print("Good job got timeout error!")
        pass
    except Exception as e:
        pytest.fail(
            f"Expected timeout error, did not get the correct error. Instead got {e}"
        )


# test_openai_azure_embedding_timeouts()


def test_openai_embedding_timeouts():
    try:
        response = embedding(
            model="text-embedding-ada-002",
            input=["good morning from litellm"],
            timeout=0.00001,
        )
        print(response)
    except openai.APITimeoutError:
        print("Good job got OpenAI timeout error!")
        pass
    except Exception as e:
        pytest.fail(
            f"Expected timeout error, did not get the correct error. Instead got {e}"
        )


# test_openai_embedding_timeouts()


def test_openai_azure_embedding():
    try:
        api_key = os.environ["AZURE_API_KEY"]
        api_base = os.environ["AZURE_API_BASE"]
        api_version = os.environ["AZURE_API_VERSION"]

        os.environ["AZURE_API_VERSION"] = ""
        os.environ["AZURE_API_BASE"] = ""
        os.environ["AZURE_API_KEY"] = ""

        response = embedding(
            model="azure/azure-embedding-model",
            input=["good morning from litellm", "this is another item"],
            api_key=api_key,
            api_base=api_base,
            api_version=api_version,
        )
        print(response)

        os.environ["AZURE_API_VERSION"] = api_version
        os.environ["AZURE_API_BASE"] = api_base
        os.environ["AZURE_API_KEY"] = api_key

    except Exception as e:
        pytest.fail(f"Error occurred: {e}")

@pytest.mark.skipif(
    os.environ.get("CIRCLE_OIDC_TOKEN") is None,
    reason="Cannot run without being in CircleCI Runner",
)
def test_openai_azure_embedding_with_oidc_and_cf():
    # TODO: Switch to our own Azure account, currently using ai.moda's account
    os.environ["AZURE_TENANT_ID"] = "17c0a27a-1246-4aa1-a3b6-d294e80e783c"
    os.environ["AZURE_CLIENT_ID"] = "4faf5422-b2bd-45e8-a6d7-46543a38acd0"

    try:
        response = embedding(
            model="azure/text-embedding-ada-002",
            input=["Hello"],
            azure_ad_token="oidc/circleci/",
            api_base="https://gateway.ai.cloudflare.com/v1/0399b10e77ac6668c80404a5ff49eb37/litellm-test/azure-openai/eastus2-litellm",
            api_version="2024-06-01",
        )
        print(response)

    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


def test_openai_azure_embedding_optional_arg(mocker):
    mocked_create_embeddings = mocker.patch.object(
        openai.resources.embeddings.Embeddings,
        "create",
        return_value=openai.types.create_embedding_response.CreateEmbeddingResponse(
            data=[],
            model="azure/test",
            object="list",
            usage=openai.types.create_embedding_response.Usage(
                prompt_tokens=1, total_tokens=2
            ),
        ),
    )
    _ = litellm.embedding(
        model="azure/test",
        input=["test"],
        api_version="test",
        api_base="test",
        azure_ad_token="test",
    )

    assert mocked_create_embeddings.called_once_with(
        model="test", input=["test"], timeout=600
    )
    assert "azure_ad_token" not in mocked_create_embeddings.call_args.kwargs


# test_openai_azure_embedding()

# test_openai_embedding()


def test_cohere_embedding():
    try:
        # litellm.set_verbose=True
        response = embedding(
            model="embed-english-v2.0",
            input=["good morning from litellm", "this is another item"],
            input_type="search_query",
        )
        print(f"response:", response)

        assert isinstance(response.usage, litellm.Usage)
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_cohere_embedding()


def test_cohere_embedding3():
    try:
        litellm.set_verbose = True
        response = embedding(
            model="embed-english-v3.0",
            input=["good morning from litellm", "this is another item"],
        )
        print(f"response:", response)

        custom_llm_provider = response._hidden_params["custom_llm_provider"]

        assert custom_llm_provider == "cohere"

    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_cohere_embedding3()


def test_bedrock_embedding_titan():
    try:
        # this tests if we support str input for bedrock embedding
        litellm.set_verbose = True
        litellm.enable_cache()
        import time

        current_time = str(time.time())
        # DO NOT MAKE THE INPUT A LIST in this test
        response = embedding(
            model="bedrock/amazon.titan-embed-text-v1",
            input=f"good morning from litellm, attempting to embed data {current_time}",  # input should always be a string in this test
            aws_region_name="us-west-2",
        )
        print(f"response:", response)
        assert isinstance(
            response["data"][0]["embedding"], list
        ), "Expected response to be a list"
        print(f"type of first embedding:", type(response["data"][0]["embedding"][0]))
        assert all(
            isinstance(x, float) for x in response["data"][0]["embedding"]
        ), "Expected response to be a list of floats"

        # this also tests if we can return a cache response for this scenario
        import time

        start_time = time.time()

        response = embedding(
            model="bedrock/amazon.titan-embed-text-v1",
            input=f"good morning from litellm, attempting to embed data {current_time}",  # input should always be a string in this test
        )
        print(response)

        end_time = time.time()
        print(f"Embedding 2 response time: {end_time - start_time} seconds")

        assert end_time - start_time < 0.1
        litellm.disable_cache()

        assert isinstance(response.usage, litellm.Usage)
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_bedrock_embedding_titan()


def test_bedrock_embedding_cohere():
    try:
        litellm.set_verbose = False
        response = embedding(
            model="cohere.embed-multilingual-v3",
            input=[
                "good morning from litellm, attempting to embed data",
                "lets test a second string for good measure",
            ],
            aws_region_name="os.environ/AWS_REGION_NAME_2",
        )
        assert isinstance(
            response["data"][0]["embedding"], list
        ), "Expected response to be a list"
        print(f"type of first embedding:", type(response["data"][0]["embedding"][0]))
        assert all(
            isinstance(x, float) for x in response["data"][0]["embedding"]
        ), "Expected response to be a list of floats"
        # print(f"response:", response)

        assert isinstance(response.usage, litellm.Usage)
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_bedrock_embedding_cohere()


def test_demo_tokens_as_input_to_embeddings_fails_for_titan():
    litellm.set_verbose = True

    with pytest.raises(
        litellm.BadRequestError,
        match="BedrockException - Bedrock Embedding API input must be type str | List[str]",
    ):
        litellm.embedding(model="amazon.titan-embed-text-v1", input=[[1]])

    with pytest.raises(
        litellm.BadRequestError,
        match="BedrockException - Bedrock Embedding API input must be type str | List[str]",
    ):
        litellm.embedding(
            model="amazon.titan-embed-text-v1",
            input=[1],
        )


# comment out hf tests - since hf endpoints are unstable
def test_hf_embedding():
    try:
        # huggingface/microsoft/codebert-base
        # huggingface/facebook/bart-large
        response = embedding(
            model="huggingface/sentence-transformers/all-MiniLM-L6-v2",
            input=["good morning from litellm", "this is another item"],
        )
        print(f"response:", response)

        assert isinstance(response.usage, litellm.Usage)
    except Exception as e:
        # Note: Huggingface inference API is unstable and fails with "model loading errors all the time"
        pass


# test_hf_embedding()


# test async embeddings
def test_aembedding():
    try:
        import asyncio

        async def embedding_call():
            try:
                response = await litellm.aembedding(
                    model="text-embedding-ada-002",
                    input=["good morning from litellm", "this is another item"],
                )
                print(response)
                return response
            except Exception as e:
                pytest.fail(f"Error occurred: {e}")

        response = asyncio.run(embedding_call())
        print("Before caclulating cost, response", response)

        cost = litellm.completion_cost(completion_response=response)

        print("COST=", cost)
        assert cost == float("1e-06")
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_aembedding()


def test_aembedding_azure():
    try:
        import asyncio

        async def embedding_call():
            try:
                response = await litellm.aembedding(
                    model="azure/azure-embedding-model",
                    input=["good morning from litellm", "this is another item"],
                )
                print(response)

                print(
                    "hidden params - custom_llm_provider",
                    response._hidden_params["custom_llm_provider"],
                )
                assert response._hidden_params["custom_llm_provider"] == "azure"

                assert isinstance(response.usage, litellm.Usage)
            except Exception as e:
                pytest.fail(f"Error occurred: {e}")

        asyncio.run(embedding_call())
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_aembedding_azure()


@pytest.mark.skip(reason="AWS Suspended Account")
def test_sagemaker_embeddings():
    try:
        response = litellm.embedding(
            model="sagemaker/berri-benchmarking-gpt-j-6b-fp16",
            input=["good morning from litellm", "this is another item"],
            input_cost_per_second=0.000420,
        )
        print(f"response: {response}")
        cost = completion_cost(completion_response=response)
        assert (
            cost > 0.0 and cost < 1.0
        )  # should never be > $1 for a single embedding call
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


@pytest.mark.skip(reason="AWS Suspended Account")
@pytest.mark.asyncio
async def test_sagemaker_aembeddings():
    try:
        response = await litellm.aembedding(
            model="sagemaker/berri-benchmarking-gpt-j-6b-fp16",
            input=["good morning from litellm", "this is another item"],
            input_cost_per_second=0.000420,
        )
        print(f"response: {response}")
        cost = completion_cost(completion_response=response)
        assert (
            cost > 0.0 and cost < 1.0
        )  # should never be > $1 for a single embedding call
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


def test_mistral_embeddings():
    try:
        litellm.set_verbose = True
        response = litellm.embedding(
            model="mistral/mistral-embed",
            input=["good morning from litellm"],
        )
        print(f"response: {response}")
        assert isinstance(response.usage, litellm.Usage)
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


def test_watsonx_embeddings():

    def mock_wx_embed_request(method: str, url: str, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {
            "model_id": "ibm/slate-30m-english-rtrvr",
            "created_at": "2024-01-01T00:00:00.00Z",
            "results": [{"embedding": [0.0] * 254}],
            "input_token_count": 8,
        }
        return mock_response

    try:
        litellm.set_verbose = True
        with patch("requests.request", side_effect=mock_wx_embed_request):
            response = litellm.embedding(
                model="watsonx/ibm/slate-30m-english-rtrvr",
                input=["good morning from litellm"],
                token="secret-token",
            )
        print(f"response: {response}")
        assert isinstance(response.usage, litellm.Usage)
    except litellm.RateLimitError as e:
        pass
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


@pytest.mark.asyncio
async def test_watsonx_aembeddings():

    def mock_async_client(*args, **kwargs):

        mocked_client = MagicMock()

        async def mock_send(request, *args, stream: bool = False, **kwags):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.json.return_value = {
                "model_id": "ibm/slate-30m-english-rtrvr",
                "created_at": "2024-01-01T00:00:00.00Z",
                "results": [{"embedding": [0.0] * 254}],
                "input_token_count": 8,
            }
            mock_response.is_error = False
            return mock_response

        mocked_client.send = mock_send

        return mocked_client

    try:
        litellm.set_verbose = True
        with patch("httpx.AsyncClient", side_effect=mock_async_client):
            response = await litellm.aembedding(
                model="watsonx/ibm/slate-30m-english-rtrvr",
                input=["good morning from litellm"],
                token="secret-token",
            )
        print(f"response: {response}")
        assert isinstance(response.usage, litellm.Usage)
    except litellm.RateLimitError as e:
        pass
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_mistral_embeddings()


@pytest.mark.skip(
    reason="Community maintained embedding provider - they are quite unstable"
)
def test_voyage_embeddings():
    try:
        litellm.set_verbose = True
        response = litellm.embedding(
            model="voyage/voyage-01",
            input=["good morning from litellm"],
        )
        print(f"response: {response}")
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


@pytest.mark.asyncio
async def test_triton_embeddings():
    try:
        litellm.set_verbose = True
        response = await litellm.aembedding(
            model="triton/my-triton-model",
            api_base="https://exampleopenaiendpoint-production.up.railway.app/triton/embeddings",
            input=["good morning from litellm"],
        )
        print(f"response: {response}")

        # stubbed endpoint is setup to return this
        assert response.data[0]["embedding"] == [0.1, 0.2]
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


@pytest.mark.parametrize("sync_mode", [True, False])
@pytest.mark.asyncio
async def test_databricks_embeddings(sync_mode):
    try:
        litellm.set_verbose = True
        litellm.drop_params = True

        if sync_mode:
            response = litellm.embedding(
                model="databricks/databricks-bge-large-en",
                input=["good morning from litellm"],
                instruction="Represent this sentence for searching relevant passages:",
            )
        else:
            response = await litellm.aembedding(
                model="databricks/databricks-bge-large-en",
                input=["good morning from litellm"],
                instruction="Represent this sentence for searching relevant passages:",
            )

        print(f"response: {response}")

        openai.types.CreateEmbeddingResponse.model_validate(
            response.model_dump(), strict=True
        )
        # stubbed endpoint is setup to return this
        # assert response.data[0]["embedding"] == [0.1, 0.2, 0.3]
    except Exception as e:
        pytest.fail(f"Error occurred: {e}")


# test_voyage_embeddings()
# def test_xinference_embeddings():
#     try:
#         litellm.set_verbose = True
#         response = litellm.embedding(
#             model="xinference/bge-base-en",
#             input=["good morning from litellm"],
#         )
#         print(f"response: {response}")
#     except Exception as e:
#         pytest.fail(f"Error occurred: {e}")
# test_xinference_embeddings()

# test_sagemaker_embeddings()
# def local_proxy_embeddings():
#     litellm.set_verbose=True
#     response = embedding(
#             model="openai/custom_embedding",
#             input=["good morning from litellm"],
#             api_base="http://0.0.0.0:8000/"
#         )
#     print(response)

# local_proxy_embeddings()
