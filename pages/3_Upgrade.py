# =====================================
# TAB 2 - ALL WEEKS SUMMARY
# =====================================
with tab2:

    st.subheader("📅 All Weeks Summary")

    for week in sorted_weeks:

        st.markdown(f"## 📅 {week}")

        week_df = df_filtered[
            df_filtered["WEEK"] == week
        ]

        summary = (
            week_df.groupby(
                ["MODEL", "IPU STATUS"]
            )
            .size()
            .unstack(fill_value=0)
        )

        # Ensure columns exist
        if "Completed" not in summary.columns:
            summary["Completed"] = 0

        if "Not Completed" not in summary.columns:
            summary["Not Completed"] = 0

        summary = summary.reset_index()

        # Total
        summary["Total"] = (
            summary["Completed"] +
            summary["Not Completed"]
        )

        # Completion %
        summary["Completion %"] = (
            summary["Completed"] /
            summary["Total"] * 100
        ).round(2)

        # Display Table
        st.dataframe(
            summary[
                [
                    "MODEL",
                    "Completed",
                    "Not Completed",
                    "Total",
                    "Completion %"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # Chart
        chart_df = summary.melt(
            id_vars=["MODEL", "Total"],
            value_vars=[
                "Completed",
                "Not Completed"
            ],
            var_name="Status",
            value_name="Count"
        )

        chart_df["Percent"] = (
            chart_df["Count"] /
            chart_df["Total"] * 100
        ).round(1)

        chart_df["Label"] = (
            chart_df["Percent"]
            .astype(str) + "%"
        )

        base = alt.Chart(chart_df).encode(
            x=alt.X("MODEL:N"),
            y=alt.Y("Count:Q"),
            xOffset="Status:N"
        )

        bars = (
            base.mark_bar()
            .encode(color="Status:N")
        )

        text = (
            base.mark_text(dy=-5)
            .encode(text="Label")
        )

        st.altair_chart(
            (bars + text).properties(height=350),
            use_container_width=True
        )

        st.divider()
