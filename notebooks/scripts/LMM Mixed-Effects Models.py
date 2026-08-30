import statsmodels.formula.api as smf

# مدل پیشرفته LMM: ارزیابی اثر مداخله، شاخص S-D-S و اثر متقابل بر مؤلفه N400
# فرمول: N400 ~ SDS_score * Group + Session + (1 + Session | Subject_ID)
# در صورتی که مدل همگرا نشود، شیب تصادفی به Intercept ساده تقلیل داده می‌شود.

formula = "N400_amplitude ~ SDS_score * Group + C(Time_Point, Treatment('Pre'))"

lmm_model = smf.mixedlm(
    formula=formula,
    data=data,
    groups=data["Subject_ID"],
    re_formula="~Time_Point" # Random Intercept + Random Slope for longitudinal tracking
)

lmm_fit = lmm_model.fit(reml=True)
print(lmm_fit.summary())

# محاسبه و چاپ اندازه‌اثر و فاصله‌های اطمینان 95%
conf_int = lmm_fit.conf_int()
print("\n95% Confidence Intervals for Fixed Effects:\n", conf_int)
