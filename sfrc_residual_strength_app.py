import streamlit as st

st.set_page_config(
    page_title="SFRC Residual Flexural Strength Tool (fR1, fR3)",
    page_icon="🧱",
    layout="wide",
)

# -----------------------------
# Fixed model parameters (as provided)
# -----------------------------
PARAMS_FR1 = dict(a=6.939, b=0.448, c=0.377, d=0.265, const=-3.823)
PARAMS_FR3 = dict(a=12.000, b=0.613, c=0.370, d=0.247, e=0.411, f=0.313, const=-1.506)

SCALE = {
    "fR1": {"k_char": 0.67, "k_design": 0.51, "gamma": 1.33},
    "fR3": {"k_char": 0.62, "k_design": 0.45, "gamma": 1.40},
}

# -----------------------------
# Fixed validity limits (dataset-based) - NOT editable
# -----------------------------
FC_MIN, FC_MAX = 22.0, 79.0          # MPa (matrix strength)
VF_PCT_MIN, VF_PCT_MAX = 0.2, 2.0    # percent
VF_DEC_MIN, VF_DEC_MAX = 0.002, 0.02 # decimal
LAMBDA_MIN, LAMBDA_MAX = 38.0, 100.0 # lf/df
FFU_MIN, FFU_MAX = 1000.0, 3200.0   # MPa

# fc - fcu conversion (rough)
FC_FROM_FCU = 0.82


def clamp_nonnegative(x: float) -> float:
    return max(0.0, x)


def fr1_pred(vf_dec: float, lf_mm: float, df_mm: float, fc_mpa: float) -> float:
    p = PARAMS_FR1
    return p["a"] * (vf_dec ** p["b"]) * ((lf_mm / df_mm) ** p["c"]) * (fc_mpa ** p["d"]) + p["const"]


def fr3_pred(vf_dec: float, lf_mm: float, df_mm: float, fc_mpa: float, ffu_mpa: float) -> float:
    p = PARAMS_FR3
    ffu_star = ffu_mpa / 1000.0
    lf_star = lf_mm / 50.0
    return (
        p["a"]
        * (vf_dec ** p["b"])
        * ((lf_mm / df_mm) ** p["c"])
        * (fc_mpa ** p["d"])
        * (ffu_star ** p["e"])
        * (lf_star ** p["f"])
        + p["const"]
    )


def in_range(x: float, lo: float, hi: float) -> bool:
    return (x >= lo) and (x <= hi)


# -----------------------------
# Sidebar navigation + format settings
# -----------------------------
page = st.sidebar.radio("Navigation", ["🧮 Calculator", "📘 Method & equations"])

st.sidebar.markdown("---")

vf_mode = st.sidebar.radio("$V_f$ input", ["Percent (%)", "Decimal"], horizontal=False)

strength_mode = st.sidebar.radio(
    "Concrete strength input",
    options=["fc", "fcu"],
    format_func=lambda x: (
        r"$f_c$ (MPa) — mean of cylindrical compressive strength"
        if x == "fc"
        else r"$f_{cu}$ (MPa) — mean of cubic compressive strength"
    ),
    horizontal=False,
)

allow_extrap = st.sidebar.checkbox("Allow extrapolation", value=True)

with st.sidebar.expander("Validated limits (fixed)", expanded=False):
    st.markdown(
        """
- $f_c$: **22 to 79 MPa** (or $f_{cu}$ converted using $f_c = 0.82\,f_{cu}$)
- $V_f$: **0.2% to 2.0%**
- $\lambda_f = l_f/d_f$: **38 to 100**
- $f_{fu}$: **1000 to 3200 MPa** (only for $f_{R,3}$)
        """
    )


# -----------------------------
# Page: Calculator
# -----------------------------
if page == "🧮 Calculator":
    st.title("SFRC residual flexural strengths")
    st.markdown("Compute $f_{R,1}$ and $f_{R,3}$ (mean, characteristic, design).")

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.subheader("Inputs")

        c_t1, c_t2 = st.columns(2)
        with c_t1:
            calc_fr1 = st.checkbox(r"Compute $f_{R,1}$", value=True)
        with c_t2:
            calc_fr3 = st.checkbox(r"Compute $f_{R,3}$", value=True)

        c1, c2 = st.columns(2)

        with c1:
            if vf_mode == "Percent (%)":
                vf_in = st.number_input(r"$V_f$ (%)", min_value=0.0, value=1.0, step=0.05, format="%.3f")
                vf_dec = vf_in / 100.0
            else:
                vf_in = st.number_input(r"$V_f$ (decimal)", min_value=0.0, value=0.01, step=0.0005, format="%.6f")
                vf_dec = vf_in

            lf = st.number_input(r"$l_f$ (mm)", min_value=0.1, value=50.0, step=1.0)
            df = st.number_input(r"$d_f$ (mm)", min_value=0.01, value=0.75, step=0.01, format="%.2f")

        with c2:
            if strength_mode == "fc":
                fc = st.number_input(r"$f_c$ (MPa)", min_value=0.1, value=40.0, step=1.0)
                fcu = None
            else:
                fcu = st.number_input(r"$f_{cu}$ (MPa)", min_value=0.1, value=50.0, step=1.0)
                fc = FC_FROM_FCU * fcu
                st.caption(rf"Converted: $f_c = 0.82\,f_{{cu}} = {fc:.2f}\,\mathrm{{MPa}}$")

            ffu = st.number_input(r"$f_{fu}$ (MPa) — only for $f_{R,3}$", min_value=0.0, value=2000.0, step=10.0)

        st.markdown("---")
        st.subheader("Validation")

        warnings = []

        # Positivity
        if vf_dec <= 0 or lf <= 0 or df <= 0 or fc <= 0:
            warnings.append("Inputs $V_f$, $l_f$, $d_f$, and $f_c$ must be positive.")

        # Vf
        if vf_mode == "Percent (%)":
            if not in_range(vf_in, VF_PCT_MIN, VF_PCT_MAX):
                warnings.append(rf"$V_f$ = {vf_in:.3f}% is outside [{VF_PCT_MIN}, {VF_PCT_MAX}]%.")
        else:
            if not in_range(vf_in, VF_DEC_MIN, VF_DEC_MAX):
                warnings.append(rf"$V_f$ = {vf_in:.6f} is outside [{VF_DEC_MIN}, {VF_DEC_MAX}].")

        # fc
        if not in_range(fc, FC_MIN, FC_MAX):
            warnings.append(rf"$f_c$ = {fc:.2f} MPa is outside [{FC_MIN}, {FC_MAX}] MPa.")

        # lambda
        lam = lf / df if df > 0 else float("nan")
        if df > 0 and not in_range(lam, LAMBDA_MIN, LAMBDA_MAX):
            warnings.append(rf"$\lambda_f = l_f/d_f$ = {lam:.2f} is outside [{LAMBDA_MIN}, {LAMBDA_MAX}].")

        # ffu
        if calc_fr3:
            if not in_range(ffu, FFU_MIN, FFU_MAX):
                warnings.append(rf"$f_{{fu}}$ = {ffu:.0f} MPa is outside [{FFU_MIN}, {FFU_MAX}] MPa.")

        if warnings:
            for w in warnings:
                st.warning(w)
        else:
            st.success("All inputs are within the validated limits.")

        can_compute = True
        if (not allow_extrap) and warnings:
            can_compute = False
            st.error("Computation stopped (extrapolation is not allowed).")

        compute_btn = st.button("Compute", type="primary", disabled=(not can_compute))

    with right:
        st.subheader("Results")

        if not (calc_fr1 or calc_fr3):
            st.info("Select at least one target.")
        elif compute_btn:
            lf_df = lf / df
            ffu_star = ffu / 1000.0
            lf_star = lf / 50.0

            if calc_fr1:
                pred1_raw = fr1_pred(vf_dec, lf, df, fc)
                pred1 = clamp_nonnegative(pred1_raw)
                f1k = SCALE["fR1"]["k_char"] * pred1
                f1d = SCALE["fR1"]["k_design"] * pred1

                with st.container(border=True):
                    st.markdown(r"## $f_{R,1}$")
                    st.metric(r"Mean prediction $f_{R,1}^{\mathrm{pred}}$ (MPa)", f"{pred1:.3f}")
                    cA, cB = st.columns(2)
                    cA.metric(r"Characteristic $f_{R,1k}$ (MPa)", f"{f1k:.3f}")
                    cB.metric(r"Design $f_{R,1d}$ (MPa)", f"{f1d:.3f}")
                    st.caption(rf"$\gamma_{{fR,1}} = {SCALE['fR1']['gamma']:.2f}$")

                    if pred1_raw < 0:
                        st.warning(r"Raw $f_{R,1}^{\mathrm{pred}}$ was negative and has been set to 0.0 MPa.")

                    with st.expander("Show calculation", expanded=False):
                        st.latex(r"f_{R,1}^{\mathrm{pred}} = 6.939\, V_f^{0.448}\, (l_f/d_f)^{0.377}\, f_c^{0.265} - 3.823")
                        st.markdown(
                            rf"- $V_f$ (decimal) = **{vf_dec:.6f}**\n"
                            rf"- $\lambda_f=l_f/d_f$ = **{lf_df:.2f}**\n"
                            rf"- $f_c$ = **{fc:.2f} MPa**\n"
                            rf"- $f_{{R,1}}^{{\mathrm{{pred}}}}$ (raw) = **{pred1_raw:.3f} MPa**"
                        )

            if calc_fr3:
                pred3_raw = fr3_pred(vf_dec, lf, df, fc, ffu)
                pred3 = clamp_nonnegative(pred3_raw)
                f3k = SCALE["fR3"]["k_char"] * pred3
                f3d = SCALE["fR3"]["k_design"] * pred3

                with st.container(border=True):
                    st.markdown(r"## $f_{R,3}$")
                    st.metric(r"Mean prediction $f_{R,3}^{\mathrm{pred}}$ (MPa)", f"{pred3:.3f}")
                    cA, cB = st.columns(2)
                    cA.metric(r"Characteristic $f_{R,3k}$ (MPa)", f"{f3k:.3f}")
                    cB.metric(r"Design $f_{R,3d}$ (MPa)", f"{f3d:.3f}")
                    st.caption(rf"$\gamma_{{fR,3}} = {SCALE['fR3']['gamma']:.2f}$")

                    if pred3_raw < 0:
                        st.warning(r"Raw $f_{R,3}^{\mathrm{pred}}$ was negative and has been set to 0.0 MPa.")

                    with st.expander("Show calculation", expanded=False):
                        st.latex(r"f_{fu}^* = f_{fu}/1000\qquad l_f^* = l_f/50")
                        st.latex(r"f_{R,3}^{\mathrm{pred}} = 12.000\, V_f^{0.613}\, (l_f/d_f)^{0.370}\, f_c^{0.247}\, (f_{fu}^*)^{0.411}\, (l_f^*)^{0.313} - 1.506")
                        st.markdown(
                            rf"- $V_f$ (decimal) = **{vf_dec:.6f}**\n"
                            rf"- $\lambda_f=l_f/d_f$ = **{lf_df:.2f}**\n"
                            rf"- $f_c$ = **{fc:.2f} MPa**\n"
                            rf"- $f_{{fu}}^*$ = **{ffu_star:.3f}**\n"
                            rf"- $l_f^*$ = **{lf_star:.3f}**\n"
                            rf"- $f_{{R,3}}^{{\mathrm{{pred}}}}$ (raw) = **{pred3_raw:.3f} MPa**"
                        )

        else:
            st.info("Enter inputs and click Compute.")


# -----------------------------
# Page: Method & equations
# -----------------------------
else:
    st.title("Method & equations")

    st.subheader("Mean prediction models")

    st.markdown(r"### $f_{R,1}$")
    st.latex(r"f_{R,1}^{\mathrm{pred}} = 6.939\, V_f^{0.448}\, \left(\frac{l_f}{d_f}\right)^{0.377}\, f_c^{0.265} - 3.823")

    st.markdown(r"### $f_{R,3}$")
    st.latex(r"f_{fu}^* = \frac{f_{fu}}{1000}\qquad l_f^* = \frac{l_f}{50}")
    st.latex(
        r"f_{R,3}^{\mathrm{pred}} = 12.000\, V_f^{0.613}\, \left(\frac{l_f}{d_f}\right)^{0.370}\, f_c^{0.247}\, (f_{fu}^*)^{0.411}\, (l_f^*)^{0.313} - 1.506"
    )

    st.subheader("Characteristic and design values")

    st.markdown(r"### $f_{R,1}$")
    st.latex(r"f_{R,1k} = 0.67\, f_{R,1}^{\mathrm{pred}}\qquad f_{R,1d} = 0.51\, f_{R,1}^{\mathrm{pred}}")
    st.latex(r"\gamma_{fR,1} = 1.33")

    st.markdown(r"### $f_{R,3}$")
    st.latex(r"f_{R,3k} = 0.62\, f_{R,3}^{\mathrm{pred}}\qquad f_{R,3d} = 0.45\, f_{R,3}^{\mathrm{pred}}")
    st.latex(r"\gamma_{fR,3} = 1.40")

    st.subheader("Input formats")
    st.markdown(
        r"""
- $V_f$ can be entered as **percent** or **decimal**.
- Concrete strength can be entered as $f_c$ or $f_{cu}$. The tool uses the rough conversion:

\[ f_c = 0.82\, f_{cu} \]
        """
    )

    st.subheader("Validated limits")
    st.markdown(
        r"""
- $f_c$: **22 to 79 MPa**
- $V_f$: **0.2% to 2.0%**
- $\lambda_f=l_f/d_f$: **38 to 100**
- $f_{fu}$: **1000 to 3200 MPa** (only for $f_{R,3}$)
        """
    )

    st.subheader("Numerical safeguard")
    st.markdown(
        r"If a raw mean prediction becomes negative due to the constant term, the tool sets it to **0.0 MPa**."
    )
