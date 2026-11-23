# A network blocker diagnosis and tests-only repair proposal

Base: #14 revision 40e86b2fb412acc3c1c681b712a544eeb1b3ee77. No runtime change in this proposal. Actual independent approval and test-baseline incorporation are required before production implementation; this document is not approval.

## Measured cause and solution probe

WSL direct curl with --noproxy '*' timed out. Direct Python HTTPS also timed out during TLS handshake. WSL environment declares a local HTTP proxy at 127.0.0.1:10808. An unauthenticated Python HTTPSConnection to that local proxy, set_tunnel('api.deepseek.com',443), and HEAD '/' returned 401 in 0.198 seconds with default TLS certificate/hostname verification. No API key or paid model request was sent during these diagnostics. This establishes a functioning transport path, not a successful authenticated model replay.

Current request_json uses direct http.client connections; ambient proxy variables do not change it. Worker intentionally strips inherited environment. Therefore retrying the current deployed configuration repeats the known direct-path failure.

## Smallest proposed runtime change after approval

Add optional Settings.proxy_url and explicit GRADEAIDE_PROXY_URL injection at the CLI boundary. Default remains None. Accept only an explicitly configured HTTP proxy on localhost/127.0.0.1/::1 with a valid nonzero port; reject userinfo, path, query, fragment and external proxy hosts. Require a HTTPS model endpoint for tunnel mode. No implicit HTTPS_PROXY inheritance, no SOCKS library or new dependency.

Use standard-library HTTPSConnection(proxy_host, proxy_port) plus set_tunnel(model_host,model_port). Preserve target TLS checks, one request, no redirects/retries, response size and existing deadlines. Never send provider Authorization in CONNECT headers. Clear proxy_url before sending settings into the networkless evaluator, together with the existing API-key replacement. Keep bubblewrap, namespace and filesystem constraints unchanged.

Reference: Python http.client documentation https://docs.python.org/3/library/http.client.html#http.client.HTTPConnection.set_tunnel. The default HTTPSConnection validates certificate and hostname. This proposal never substitutes an unverified SSL context.

## Proposed tests and review scope

Seven tests in test/offline/test_broker_proxy.py cover explicit routing, credentials excluded from tunnel headers, ignored ambient proxies, invalid configuration, no retries/redirects, certificate failure, explicit CLI injection and proxy absence from sandbox settings. Requirements/locators/implementation scope are recorded in docs/verification/test-plans/explicit-broker-proxy.json and test-map.yaml. Tests use synthetic values/mocks and no paid provider calls. A real no-key default-TLS CONNECT was probed separately as above.

Actual pre-implementation baseline: seven tests collected, expected failures/errors because proxy_url does not exist; 20 errors include subcases. Schema passes. No green assertion or completed implementation is claimed. Existing settings/transport/evaluator sources are unchanged.

## Required next decisions

Existing independent member reviews this exact tests-only head and scope; B arranges its reviewed incorporation into the proper test-baselines ancestry. Do not implement and then backfill approval. This proposal is stacked on #14 for review, not itself proof of an approved test-baselines merge. No new allowance for #13's historical deviation is claimed.

After actual approval, implementation must be a separate change retaining exact reviewed test bytes; refresh API/contract/AI-use evidence and rerun all prior suites. A new deployed candidate then needs at most five explicitly authorized worker calls, USD 0.05 each / USD 0.25 total, stopping on first failure. Final semantic acceptance remains C/D's decision; previous rejected 25-call evidence is not promoted. No additional paid call was made in this proposal.
