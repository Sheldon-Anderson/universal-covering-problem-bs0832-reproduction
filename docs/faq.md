# FAQ

## Does the repository contain all certificate data?

Yes. The required archives are bundled in `certificate/final_chain/`.

## Does the public replay rerun the original geometric search?

No. The public scripts replay theorem-relevant checks from the bundled certificate records. They do not rerun the original search and do not regenerate the certificate records from scratch.

## What is the difference between certificate verification and repository check?

`verify_certificate.py` checks the certificate-chain archives. `check_repository.py` checks the public release package and also runs the main certificate verification internally.

## What is certificate-chain replay?

`replay_certificate_chain.py` replays the four certificate-chain components without README, layout, or release-wording checks.

## What do the component-level verification commands do?

They isolate one component: per-record evidence, construction audit, witness construction, or final adjudication. They are useful for locating the source of a component failure, but they do not replace the main certificate verification.

## Why is the witness-domain area bound larger than 0.83201?

That value is local to the witness domains. The global certified threshold is obtained after combining all local records over the finite cover.

## Why do archive members still mention v133 through v136?

Those internal names are raw certificate-record provenance labels. The public roles are per-record evidence, construction audit, witness construction, and final adjudication.

## What does `ucbs` mean?

It is the Python package root for the universal-cover Brass-Sharifi certificate verifier.

## Does this solve the nonconvex problem?

No. The scope is the convex Brass-Sharifi three-test-set certificate setting.

## Is a proof-assistant formalization included?

No. The repository contains a finite certificate and Python replay checks.
