# 9MM token list

The tokens 9MM lists on PulseChain (chain id 369), with their logos. The 9MM app at
[app.9mm.pro](https://app.9mm.pro) builds its token list from here, and any wallet or app may read it.

| File | What it is |
| --- | --- |
| [`9mm-tokenlist.json`](9mm-tokenlist.json) | The 9MM list: the tokens the app shows with their logo and without a warning |
| [`9mm-tokenlist-extended.json`](9mm-tokenlist-extended.json) | A longer list of PulseChain tokens, for apps that want more |
| [`token-logo/`](token-logo) | Each listed token's logo, named by its address: `token-logo/<address>.png` |

Both lists follow the [Uniswap token list](https://tokenlists.org) format. Read them raw:
`https://raw.githubusercontent.com/ninemm-pro/app-tokens/main/9mm-tokenlist.json`.

## What listing does

A listed token shows in the 9MM app with its logo, and without the "not on the 9MM list" warning.

Listing does **not** make a token tradeable, and does not give it a price. Any token in a 9MM pool
can already be traded by pasting its address, and a token with no pool yet can have its first pool
created on Add liquidity. A token's dollar price comes from the liquidity in its pools.

Listing tells people the address is the token they are looking for, so every request is checked
before it is merged.

## Asking for a token to be listed

Open a pull request that changes two things:

1. **Add the token at the end of the `tokens` array in `9mm-tokenlist.json`:**

   ```json
   {
     "chainId": 369,
     "address": "0x15D38573d2feeb82e7ad5187aB8c1D52810B1f07",
     "name": "USD Coin from Ethereum",
     "symbol": "USDC",
     "decimals": 6,
     "logoURI": "https://raw.githubusercontent.com/ninemm-pro/app-tokens/main/token-logo/0x15D38573d2feeb82e7ad5187aB8c1D52810B1f07.png"
   }
   ```

2. **Add its logo** as `token-logo/<address>.png`: square, at least 128 × 128 pixels, under 200 KB.

In the pull request, say who you are and link the project's own website or account that names this
address as its token.

### What is checked before a pull request is merged

- The address is a token contract on PulseChain, and `name`, `symbol` and `decimals` match what the
  contract itself reports.
- The address is not already on the list.
- The project's own website or account names this address.
- The logo is the project's own, and the file is a PNG named by the address.

A request can be refused without a reason. Tokens that share a symbol are listed by their own name
and address; the list never calls one of them the real one.
