# =====================================
# ALL WEEKS SUMMARY
# =====================================
with tab2:

    st.subheader("📅 Weekly Summary")

    if df_filtered.empty:
        st.warning("⚠️ No data available")
    else:

        weekly_summary = (
            df_filtered.groupby(
                ["WEEK", "IPU STATUS"]
            )
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        # Ensure columns exist
        if "Completed" not in weekly_summary.columns:
            weekly_summary["Completed"] = 0

        if "Not Completed" not in weekly_summary.columns:
            weekly_summary["Not Completed"] = 0

        # Totals
        weekly_summary["Total"] = (
            weekly_summary["Completed"]
            + weekly_summary["Not Completed"]
        )

        # Percentage
        weekly_summary["Completion %"] = (
            weekly_summary["Completed"]
            / weekly_summary["Total"]
        ).fillna(0) * 100

        weekly_summary["Completion %"] = (
            weekly_summary["Completion %"]
            .round(2)
        )

        # Sort weeks descending
        weekly_summary = weekly_summary.sort_values(
            by="WEEK",
            ascending=False
        )

        # Display table
        st.dataframe(
            weekly_summary,
            use_container_width=True,
            hide_index=True
        )

        # =====================================
        # TREND CHART
        # =====================================
        st.subheader("📈 Weekly Completion Trend")

        if len(weekly_summary) > 0:

            chart = alt.Chart(
                weekly_summary
            ).mark_line(point=True).encode(
                x=alt.X("WEEK:N", sort=None),
                y=alt.Y("Completion %:Q"),
                tooltip=[
                    "WEEK",
                    "Completed",
                    "Not Completed",
                    "Completion %"
                ]
            )

            st.altair_chart(
                chart,
                use_container_width=True
            )
        else:
            st.info("No weekly trend data available")
