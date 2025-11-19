# Chromia x ACP demo

Blog Post: https://superoo7.com/posts/virtuals-acp-chromia/

## .env.local setup
```
SELLER_WALLET_PRIVATE_KEY=
SELLER_ENTITY_ID=
SELLER_AGENT_WALLET_ADDRESS=

BUYER_WALLET_PRIVATE_KEY=
BUYER_ENTITY_ID=
BUYER_AGENT_WALLET_ADDRESS=

CHR_PRIV_KEY=
```

## How to run it

```sh
uv init
uv pip install

# In the first terminal, start the Chromia node (run in the background):
(cd agent-job && chr node start)

# In a second terminal, start the seller agent:
uv run acp/seller.py

# (Optional) In a third terminal, start the buyer agent:
uv run acp/buyer.py
```

