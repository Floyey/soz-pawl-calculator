import streamlit as st

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="PAWL - Calculateur de vente", layout="wide")

TARGET = 300_000

ITEMS = [
    {
        "key": "basic",
        "label": "Banal",
        "price": 160,
        "img": "https://raw.githubusercontent.com/SOZ-Faut-etre-Sub/SOZ-FiveM-Assets/oss/images/items/cabinet_zkea_1.webp",
        "priority": 0,
    },
    {
        "key": "nice",
        "label": "Joli",
        "price": 500,
        "img": "https://raw.githubusercontent.com/SOZ-Faut-etre-Sub/SOZ-FiveM-Assets/oss/images/items/cabinet_zkea_2.webp",
        "priority": 1,
    },
    {
        "key": "sublime",
        "label": "Sublime",
        "price": 1600,
        "img": "https://raw.githubusercontent.com/SOZ-Faut-etre-Sub/SOZ-FiveM-Assets/oss/images/items/cabinet_zkea_3.webp",
        "priority": 2,
    },
    {
        "key": "divine",
        "label": "Divin",
        "price": 6000,
        "img": "https://raw.githubusercontent.com/SOZ-Faut-etre-Sub/SOZ-FiveM-Assets/oss/images/items/cabinet_zkea_4.webp",
        "priority": 3,
    },
]


# -------------------------
# STATE HELPERS
# -------------------------
@st.cache_data(show_spinner=False)
def cached_combos(stocks_tuple, target, keep_one_each: bool):
    stocks = dict(stocks_tuple)
    return calculate_sales_combinations(ITEMS, stocks, target, top_k=3, keep_one_each=keep_one_each)


def request_open_dialog():
    st.session_state.dialog_trigger += 1


if "dialog_trigger" not in st.session_state:
    st.session_state.dialog_trigger = 0
if "dialog_consumed" not in st.session_state:
    st.session_state.dialog_consumed = 0


# -------------------------
# LOGIQUE COMBINAISONS
# -------------------------
def calculate_sales_combinations(items, stocks, target, top_k=3, keep_one_each=True):
    if keep_one_each:
        sellable = {k: max(v - 1, 0) for k, v in stocks.items()}
    else:
        sellable = dict(stocks)

    resolver = min(items, key=lambda x: x["price"])
    resolver_key = resolver["key"]
    resolver_price = resolver["price"]

    others = sorted(
        [it for it in items if it["key"] != resolver_key],
        key=lambda x: x["price"],
        reverse=True
    )

    prio_keys = [it["key"] for it in sorted(items, key=lambda x: x.get("priority", 999))]

    results = []

    def comb_sort_key(comb):
        return tuple(-comb.get(k, 0) for k in prio_keys)

    def push_result(comb):
        results.append(comb)
        if len(results) > top_k:
            results.sort(key=comb_sort_key)
            del results[top_k:]

    def dfs(i, remaining, current):
        if i == len(others):
            if remaining % resolver_price != 0:
                return
            qty = remaining // resolver_price
            if qty <= sellable.get(resolver_key, 0):
                comb = dict(current)
                comb[resolver_key] = qty
                push_result(comb)
            return

        it = others[i]
        key, price = it["key"], it["price"]
        max_qty = min(sellable.get(key, 0), remaining // price)

        for qty in range(max_qty + 1):
            current[key] = qty
            dfs(i + 1, remaining - qty * price, current)
        current.pop(key, None)

    dfs(0, target, {})
    return results


# -------------------------
# UI STYLES (GRID RESPONSIVE)
# -------------------------
st.markdown(
    """
<style>
/* Cards */
.card {
  border: 1px solid rgba(49, 51, 63, 0.2);
  border-radius: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
}

.card-title {
  display:flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}

.card-title .name {
  font-weight: 700;
  font-size: 1rem;
}

.card-title .price {
  opacity: 0.8;
  font-size: 0.95rem;
}

div[data-baseweb="input"] input {
  max-width: 140px !important;
}

.center-img {
  display:flex;
  justify-content:center;
  margin: 10px 0 6px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# HEADER
# -------------------------
st.title("Calculateur de vente de meubles")

# -------------------------
# INPUTS GRID
# -------------------------
cols = st.columns(len(ITEMS), gap="large")

for col, item in zip(cols, ITEMS):
    with col:
        st.markdown(
            f"""
            <div class="card-title">
                <div class="name">{item["label"]}</div>
                <div class="price">${item["price"]:,d} / unité</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="center-img">', unsafe_allow_html=True)
        st.image(item["img"], width=200)

        st.markdown('Stock')
        st.number_input(
            label="Stock",
            min_value=0,
            step=1,
            key=f"stock_{item['key']}",
            label_visibility="collapsed",
        )

        st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# LIVE TOTAL
# -------------------------
stocks = {item["key"]: int(st.session_state.get(f"stock_{item['key']}", 0)) for item in ITEMS}
total_value = sum(stocks[item["key"]] * item["price"] for item in ITEMS)
can_compute = total_value >= TARGET

c1, c2, c3 = st.columns([1.2, 1, 1])
with c1:
    st.metric("Valeur totale du stock (estimation)", f"${total_value:,d}")
with c2:
    st.metric("Objectif", f"${TARGET:,d}")
with c3:
    delta = total_value - TARGET
    st.metric("Marge", f"${delta:,d}")

st.divider()

# -------------------------
# CTA
# -------------------------
st.button(
    f"Trouver des combinaisons (exact ${TARGET:,d})",
    disabled=not can_compute,
    use_container_width=True,
    type="primary",
    on_click=request_open_dialog if can_compute else None,
)

# -------------------------
# MODAL
# -------------------------
if st.session_state.dialog_trigger > st.session_state.dialog_consumed:
    st.session_state.dialog_consumed = st.session_state.dialog_trigger

    @st.dialog(f"Combinaisons possibles (objectif exact ${TARGET:,d})", width="large")
    def show_combinaisons_dialog():
        stocks_tuple = tuple(sorted(stocks.items()))

        combos = cached_combos(stocks_tuple, TARGET, True)

        if not combos:
            combos = cached_combos(stocks_tuple, TARGET, False)

        if not combos:
            return

        if len(combos) == 1:
            st.caption("Affichage de la meilleure combinaison")
        else:
            st.caption(f"Affichage des {len(combos)} meilleures combinaisons")

        for idx, comb in enumerate(combos, start=1):
            st.subheader(f"Combinaison #{idx}")
            row = st.columns(len(ITEMS))

            for col, item in zip(row, ITEMS):
                with col:
                    qty = comb.get(item["key"], 0)
                    st.image(item["img"], width=200)
                    st.markdown(f"À vendre : **{qty}**")
                    st.caption(f"Valeur : ${qty * item['price']:,d}")

    show_combinaisons_dialog()
