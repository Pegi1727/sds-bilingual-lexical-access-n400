###############################################################################
## replication_analysis.R
##
## Authoritative reproduction script for:
##   "From L1-Mediated Translation to Direct L2 Conceptualization"
##
## This script reproduces the ENTIRE analysis pipeline of the paper:
##   1. Data loading  (workbook (2).xlsx via readxl, CSV fallback)
##   2. Descriptive statistics
##   3. GEE models (geepack::geeglm, Po / exchangeable) for
##) for
##      count outcomes L1_Req and L1_Calque
##   4. Linear Mixed Models (lme4::lmer + lmerTest) for Latency, Fluency,
##      N400_Amp with random intercept (1 | ID)
##   5. Mediation / path analysis (lavaan, 5000 bootstrap resamples):
##      Group -> Delta_N400 -> Delta_Behavioral
##   6. Publication-quality ggplot2 figures (Figure 1, 2, 3)
##
## Design of the study (per paper): 40 participants x 3 time points
## (Months 1, 3, 6); Experimental Group (EG) vs Control Group (CG), N = 120 rows.
##
## Best practices used:
##   - pacman for package management (auto-install / auto-load)
##   - tidyverse idiom throughout (dplyr, tidyr, purrr, ggplot2)
##   - modular, user-callable functions (no hard-coded magic numbers)
##   - every result table exported as CSV so supplementary tables are
##     always fully generated and internally consistent
##
## Run with:  source("replication_analysis.R")
##            run_all()          # executes the complete pipeline
###############################################################################

## -----------------------------------------------------------------------------
## 0. SETUP --------------------------------------------------------------------
## -----------------------------------------------------------------------------

## pacman manages installation and loading in one step ------------------------
if (!requireNamespace("pacman", quietly = TRUE)) {
  install.packages("pacman")
}
pacman::p_load(
  readxl,      # reading .xlsx workbooks
  tidyverse,   # dplyr, tidyr, ggplot2, purrr, readr, forcats
  geepack,     # Generalized Estimating Equations (geeglm)
  lme4,        # Linear Mixed Models (lmer)
  lmerTest,    # p-values / Satterthwaite df for lmer
  lavaan,      # SEM: mediation / path analysis with bootstrapping
  broom,       # tidy model outputs
  bro,     # estimated marginal tidy lmer outputs
  emmeans,     # estimated marginal means (optional follow-ups)
  cowplot      # assembling multi-panel figures
)

## Project paths (edit BASE_DIR if running elsewhere) --------------------------
BASE_DIR <- getwd()
DATA_XLSX <- file.path(BASE_DIR, "workbook (2).xlsx")
OUT_DIR   <- file.path(BASE_DIR, "replication_output")
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

## Reproducibility -------------------------------------------------------------
set.seed(20240501)   # fixed seed: GEE start values, lmer, lavaan bootstrap
N_BOOT  <- 5000      # bootstrap resamples for mediation (per protocol)
ALPHA   <- 0.05

## Theme used for all publication-quality figures ------------------------------
theme_paper <- theme_bw(base_size = 12) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(linewidth = 0.25, colour = "grey85"),
    strip.background = element_rect(fill = "grey92", colour = NA),
    legend.position  = "top",
    plot.title       = element_text(face = "bold"),
    plot.caption     = element_text(size = 8, colour = "grey30")
  )

## Consistent group colours (EG = experimental, CG = control) ------------------
group_cols <- c(EG = "#D95F02", CG = "#1B9E77")

## -----------------------------------------------------------------------------
## 1. DATA LOADING -------------------------------------------------------------
## -----------------------------------------------------------------------------

#' Load the study data: prefer 'workbook (2).xlsx' (sheet Raw_Data),
#' fall back to any CSV with the same variable names.
#' @return A tibble with ID, Group (factor EG/CG), Month (factor),
#'         L1_Req, L1_Calque, Latency, Fluency, N400_Amp
load_data <- function(xlsx_path = DATA_XLSX) {
  required <- c("ID", "Group", "Month", "L1_Req", "L1_Calque",
                "Latency", "Fluency", "N400_Amp")

  if (file.exists(xlsx_path)) {
    dat <- readxl::read_excel(xlsx_path, sheet = "Raw_Data")
    message("Loaded data from XLSX: ", xlsx_path)
  } else {
    ## ---- CSV fallback: look for any *.csv in BASE_DIR with required vars ----
    csvs <- list.files(BASE_DIR, pattern = "\\.csv$", full.names = TRUE)
    dat  <- NULL
    for (f in csvs) {
      cand <- tryCatch(readr::read_csv(f, show_col_types = FALSE),
                       error = function(e) NULL)
      if (!is.null(cand) && all(required %in% names(cand))) { dat <- cand; break }
    }
    if (is.null(dat)) stop("No XLSX or CSV with required columns found.")
    message("Loaded data from CSV fallback: ", f)
  }

  dat %>%
    ## type safety / factor coding exactly as in the paper ------------------
    mutate(
      ID    = factor(ID),
      Group = factor(Group, levels = c("CG", "EG")),   # CG = reference
      Month = factor(Month, levels = c("1", "3", "6")) # ordered time points ordered time points
    ) %>%
    arrange(ID, Month) %>%
    ## ----------------------------------------------------
    { stopifnot(all(required %in% names(.)),
                !any(is.na(select(., all_of(required))))) }
}

## -----------------------------------------------------------------------------
## 2. DESCRIPTIVE STATISTICS ---------------------------------------------------
## -----------------------------------------------------------------------------

#' Full descriptive statistics table (mean, sd, median, IQR, min, max, n)
#' crossed by Group x Month for every dependent variable.
compute_descriptives <- function(dat) {
  dvars <- c("L1_Req", "L1_Calque", "Latency", "Fluency", "N400_Amp")
  dat %>%
    group_by(Group, Month) %>%
    summarise(
      across(all_of(dvars),
             list(n = ~sum(!is.na(.x)),
                  mean = ~mean(.x, na.rm = TRUE),
                  sd   = ~sd(.x, na.rm = TRUE),
                  median = ~median(.x, na.rm = TRUE),
                  iqr = ~IQR(.x, na.rm = TRUE),
                  min = ~min(.x, na.rm = TRUE),
                  max = ~max(.x, na.rm = TRUE)),
             .names = "{.col}__{.fn}"),
      .groups = "drop"
    ) %>%
    arrange(Month, Group)
}

#' Correlation matrix (Pearson) of all continuous measures.
compute_correlations <- function(dat) {
  dvars <- c("L1_Req", "L1_Calque", "Latency", "Fluency", "N400_Amp")
  cor(dat %>% select(all_of(dvars)), use = "pairwise.complete.obs",
      method = "pearson")
}

## -----------------------------------------------------------------------------
## 3. GEE MODELS (count outcomes) ----------------------------------------------
## -----------------------------------------------------------------------------

#' Fit GEE models for one count outcome with both correlation structures.
#' Model: outcome ~ Group * Month   (clustering = participant ID)
#' @param cor_struct either "ar1" or "exchangeable"
fit_gee <- function(dat, outcome, cor_struct = c("ar1", "exchangeable")) {
  cor_struct <- match.arg(cor_struct)
  form <- as.formula(paste(outcome, "~ Group * Month"))
  m <- geepack::geeglm(
    form,
    data    = dat,
    family  = poisson(link = "log"),
    id      = ID,
    waves   = Month,
    corstr  = cor_struct
  )
  tidy(m, conf.int = TRUE, conf.level = 1 - ALPHA, exponentiate = TRUE) %>%
    mutate(Outcome = outcome, CorrStruct = cor_struct,
           Model = "GEE Poisson (IRR scale)")
}

#' Run all four GEE models (2 outcomes x 2 correlation structures)
#' and export one tidy supplementary table.
run_gee_all <- function(dat) {
  out <- bind_rows(
    purrr::cross2(c("L1_Req", "L1_Calque"), c("ar1", "exchangeable")) %>%
      purrr::map_dfr(~ fit_gee(dat, .x[[1]], .x[[2]]))
  )
  ## model comparison: QIC per model, to justify the chosen working correlation
  qic_tab <- purrr::map2_dfr(
    rep(c("L1_Req", "L1_Calque"), each = 2),
    rep(c("ar1", "exchangeable"), 2),
    ~ {
      form <- as.formula(paste(.x, "~ Group * Month"))
      m <- geepack::geeglm(form, data = dat, family = poisson(),
                           id = ID, waves = Month, corstr = .y)
      tibble(Outcome = .x, CorrStruct = .y, QIC = geepack::QIC(m)[1])
    })
  list(table = out, qic = qic_tab)
}

## -----------------------------------------------------------------------------
## 4. LINEAR MIXED MODELS (continuous outcomes) --------------------------------
## -----------------------------------------------------------------------------

#' Fit an LMM: outcome ~ Group * Month + (1 | ID), Satterthwaite p-values.
fit_lmm <- function(dat, outcome) {
  form <- as.formula(paste(outcome, "~ Group * Month + (1 | ID)"))
  m <- lme4::lmer(form, data = dat, REML = TRUE)
  as.data.frame(lmerTest::anova(m)) %>%                 # fixed-effect tests
    rownames_to_column("Effect") %>%
    mutate(Outcome = outcome, Model = "LMM (1|ID), Satterthwaite df")
}

#' Run LMMs for all three continuous outcomes and export the table.
run_lmm_all <- function(dat) {
  tab <- bind_rows(purrr::map(c("Latency", "Fluency", "N400_Amp"),
                              ~ fit_lmm(dat, .x)))
  ## full coefficient table (estimates, SE, CIs) ------------------------------
efs <- bind_rows(purrr::map(
    c("Latency", "FluFluency", "N400_Amp"),
    ~ tidy(lme4::lmer(as.formula(paste(.x, "~ Group * Month + (1|ID)")),
                      data = dat, REML = TRUE), effects = "fixed",
           conf.int = TRUE) %>% mutate(Outcome = .x)))
  list(anova = tab, coefs = coefs)
}

## -----------------------------------------------------------------------------
## 5. MEDIATION / PATH ANALYSIS (lavaan, 5000 bootstrap resamples) -------------
## -----------------------------------------------------------------------------

#' Compute person-level change scores and fit the mediation model
#'   Group -> Delta_N400 -> Delta_Behavioral
#' Delta scores are computed within participant from Month 1 (baseline)
#' to Month 6:  Delta_X = X(Month 6) - X(Month 1).
prepare_deltas <- function(dat) {
  dat %>%
    select(ID, Group, Month, Latency, Fluency, N400_Amp) %>%
    pivot_wider(names_from = Month,
                values_from = c(Latency, Fluency, N400_Amp),
                names_glue = "{.value}_{Month}") %>%
    mutate(
      Delta_N400   = N400_Amp_6 - N400_Amp_1,   # less negative = reduced N400
      Delta_Behav  = Fluency_6 - Fluency_1,     # behavioural gain
      Delta_Behav2 = Latency_1 - Latency_6      # RT improvement (lower = better)
    ) %>%
    mutate(GroupNum = as.numeric(Group == "EG")) # EG = 1, CG = 0 for lavaan
}

#' Fit the lavaan mediation model with bias-corrected bootstrap CIs.
#' Paths:  a = Group -> Delta_N400 ; b = Delta_N400 -> Delta_Behavioral ;
#'         c' = direct effect ;  ab = indirect effect ;  c = total effect.
run_mediation <- function(dat, n_boot = N_BOOT) {
  d <- prepare_deltas(dat)
  model <- '
    # --- measurement of the behavioural change outcome -----------------------
    Delta_Behavioral =~ 1*Delta_Behav + Delta_Behav2

    # --- structural paths -----------------------------------------------------
    Delta_N400 ~ a*GroupNum                 # path a: Group -> Delta_N400
    Delta_Behavioral ~ b*Delta_N400 + cprime*GroupNum   # b + direct path c-prime

    # --- defined effects ------------------------------------------------------
    indirect := a*b          # indirect (mediated) effect
    direct   := cprime       # direct effect
    total    := cprime + a*b # total effect
    prop_mediated := (a*b) / (cprime + a*b)
*b) / (cprime + a*b)
  '
  fit <- lavaan::sem",
                     bootstrap = n_boot, fixed.x = FALSE)
  list(
    fit      = fit,
    paths    = lavaan::parameterEstimates(fit, boot.ci.type = "bca.simple",
                                          standardized = TRUE),
    fitmeas  = lavaan::fitMeasures(fit, c("chisq", "df", "pvalue",
                                          "cfi", "tli", "rmsea",
                                          "rmsea.ci.upper", "srmr"))
  )
}

## -----------------------------------------------------------------------------
## 6. FIGURES (ggplot2, publication quality) -----------------------------------
## -----------------------------------------------------------------------------

#' Figure 1: Longitudinal trajectories of L1-mediated translation counts
#' (L1_Req, L1_Calque) by Group across Months — mean +/- SE line plots.
make_figure1 <- function(dat) {
  dat %>%
    select(ID, Group, Month, L1_Req, L1_Calque) %>%
    pivot_longer(c(L1_Req, L1_Calque),
                 names_to = "Measure", values_to = "Count") %>%
    mutate(Measure = recode(Measure,
                            L1_Req    = "L1 Requests",
                            L1_Calque = "L1 Calques")) %>%
    group_by(Group, Month, Measure) %>%
    summarise(mean = mean(Count), se = sd(Count) / sqrt(n()),
              .groups = "drop") %>%
    ggplot(aes(Month, mean, colour = Group, group = Group)) +
    geom_errorbar(aes(ymin = mean - se, ymax = mean + se),
                  width = 0.12, linewidth = 0.5) +
    geom_line(linewidth = 0.9) +
    geom_point(size = 2.6) +
    facet_wrap(~ Measure, scales = "free_y") +
    scale_colour_manual(values = group_cols) +
    labs(title = "Figure 1. L1-Mediated Translation over Time",
         subtitle = "Mean \u00B1 SE of L1 requests and calques by group",
         x = "Month", y = "Mean count per participant",
         colour = "Group", caption = "EG = Experimental; CG = Control") +
    theme_paper
}

#' Figure 2: Behavioural + ERP outcomes (Latency, Fluency, N400_Amp) by
#' Group x Month — mean +/- SE, raincloud-style box + point overlay.
make_figure2 <- function(dat) {
  dat %>%
    pivot_longer(c(Latency, Fluency, N400_Amp),
                 names_to = "Measure", values_to = "Value") %>%
    mutate(Measure = recode(Measure,
                            Latency  = "Response Latency (s)",
                            Fluency  = "Fluency (score)",
                            N400_Amp = "N400 Amplitude (\u00B5V)")) %>%
    ggplot(aes(Month, Value, fill = Group)) +
    geom_boxplot(alpha = 0.45, outlier.shape = NA,
                 position = position_dodge(0.7), width = 0.6) +
    stat_summary(aes(colour = Group), fun = mean, geom = "point",
                 position = position_dodge(0.7), size = 2.6) +
    stat_summary(aes(colour = Group), fun.data = mean_se, geom = "errorbar",
                 width = 0.12, position = position_dodge(0.7), linewidth = 0.5) +
    facet_wrap(~ Measure, scales = "free_y") +
    scale_fill_manual(values = group_cols) +
    scale_colour_manual(values = group_cols) +
    labs(title = "Figure 2. Behavioural and ERP Outcomes across Time",
         subtitle = "Boxplots (IQR) with mean \u00B1 SE overlay",
         x = "Month", y = "Value", fill = "Group", colour = "Group") +
    theme_paper
}

#' Figure 3: Mediation model — Group -> Delta_N400 -> Delta_Behavioral.
#' (a) scatter with fitted regression of Delta_N400 on Delta_Behavioral by
#'     group; (b) standardised path diagram rendered with ggplot.
make_figure3 <- function(med, deltas) {
  ## panel A: relationship between neural and behavioural change --------------
  pA <- ggplot(deltas,
               aes(Delta_N400, Delta_Behav, colour = Group)) +
    geom_point(size = 2.2, alpha = 0.8) +
    geom_smooth(method = "lm", se = TRUE, linewidth = 0.8) +
    scale_colour_manual(values = group_cols) +
    labs(title = "(a) \u0394N400 vs \u0394Fluency",
         x = "\u0394 N400 amplitude (Month 6 \u2212 Month 1, \u00B5V)",
         y = "\u0394 Fluency (Month 6 \u2212 Month 1)",
         colour = "Group") +
    theme_paper

  ## panel B: standardised path diagram ---------------------------------------
  est <- med$paths %>%
    filter(label %in% c("a", "b", "cprime", "indirect", "total"))
  get_est <- function(l) est$pstd[est$label == l]
  nodes <- tibble(
    x    = c(0, 0.5, 1, 0.5),
    y    = c(1, 0, 1, 0.55),
    lab  = c("Group\n(EG vs CG)", "Total effect\n(Total)",
             "\u0394 N400\n(neural change)", "\u0394 Behavioral\n(gain)"),
    typ  = c("X", "E", "M", "Y")
  )
  edges <- tibble(
    x    = c(0,    1,    0,    0.5),
    y    = c(1,    1,    1,    0),
    xend = c(0.85, 0.15, 0.15, 0.5),
    yend = c(0.45, 0.45, 0.45, 0.55),
    lab  = c(sprintf("a (std \u03B2 = %.2f)", get_est("a")),
             sprintf("b (std \u03B2 = %.2f)", get_est("b")),
             sprintf("c' (std \u03B2 = %.2f)", get_est("cprime")),
             sprintf("Indirect ab = %.2f", get_est("indirect")))
  )
  pB <- ggplot() +
    geom_segment(data = edges, aes(x, y, xend = xend, yend = yend),
                 arrow = arrow(length = unit(0.22, "cm"), type = "closed"),
                 linewidth = 0.8, colour = "grey25") +
    geom_label(data = edges, aes((x + xend) / 2, (y + yend) / 2, label = lab),
               size = 3.1, fill = "white", label.size = 0) +
    geom_label(data = nodes, aes(x, y, label = lab, fill = typ),
               size = 3.4, colour = "white", fontface = "bold",
               label.padding = unit(0.35, "lines"), show.legend = FALSE) +
    scale_fill_manual(values = c(X = "# +
    scale_fill_manual(values = c(X = "#F02",
                                 Y = "#1B9E77", E = "#666666")) +
    xlim(-0.15, 1.15) + ylim(-0.1, 1.2) +
    labs(title = "(b) Mediation: Group \u2192 \u0394N400 \u2192 \u0394Behavioral") +
    theme_void()

  cowplot::plot_grid(pA, pB, nrow = 2, rel_heights = c(1, 0.9),
                     labels = "", align = "v") +
    ggtitle("Figure 3. Neural Change Mediates Behavioural Gains")
}

## -----------------------------------------------------------------------------
## 7. ORCHESTRATION -------------------------------------------------------------
## -----------------------------------------------------------------------------

#' Run the complete reproduction pipeline and write every output file.
run_all <- function(dat = load_data()) {

  ## ---- (2) descriptives -----------------------------------------------------
  desc <- compute_descriptives(dat)
  corr <- compute_correlations(dat)
  readr::write_csv(desc, file.path(OUT_DIR, "01_descriptive_statistics.csv"))
  ## required supplementary table ----------------------------------------------
  readr::write_csv(as.data.frame(corr) %>% rownames_to_column("Variable"),
                   file.path(OUT_DIR, "03_correlation_matrix.csv"))

  ## ---- (3) GEE ---------------------------------------------------------------
  gee <- run_gee_all(dat)
  readr::write_csv(gee$table, file.path(OUT_DIR, "02_gee_results.csv"))
  readr::write_csv(gee$qic,   file.path(OUT_DIR, "02b_gee_qic.csv"))

  ## ---- (4) LMM ---------------------------------------------------------------
  lmm <- run_lmm_all(dat)
  readr::write_csv(lmm$anova, file.path(OUT_DIR, "04_lmm_anova.csv"))
  readr::write_csv(lmm$coefs, file.path(OUT_DIR, "04b_lmm_coefs.csv"))

  ## ---- combined GEE + LMM supplementary table (required file) ----------------
  ## unify the two families into one tidy results table:
  gee_comb <- gee$table %>%
    select(Outcome, CorrStruct, term, estimate = estimate,
           std.error, statistic, p.value, conf.low, conf.high) %>%
    mutate(Family = "GEE Poisson")
  lmm_comb <- lmm$coefs %>%
    select(Outcome, term, estimate, std.error, statistic,
           p.value, conf.low, conf.high) %>%
    mutate(CorrStruct = NA, Family = "LMM Gaussian")
  combined <- bind_rows(gee_comb, lmm_comb) %>%
    select(Family, Outcome, CorrStruct, everything())
  ## ---- REQUIRED OUTPUT: 02_gee_lmm_results.csv -------------------------------
  readr::write_csv(combined,
                   file.path(OUT_DIR, "02_gee_lmm_results.csv"))

  ## ---- (5) mediation ----------------------------------------------------------
  med <- run_mediation(dat, n_boot = N_BOOT)
  readr::write_csv(med$paths,   file.path(OUT_DIR, "05_mediation_paths.csv"))
  readr::write_csv(as.data.frame(as.list(med$fitmeas)) %>%
                     mutate(Measure = names(med$fitmeas), .before = 1),
                   file.path(OUT_DIR, "05b_mediation_fitmeasures.csv"))

  ## ---- (6) figures -------------------------------------------------------------
  deltas <- prepare_deltas(dat)
  ggsave(file.path(OUT_DIR, "Figure_1.png"), make_figure1(dat),
         width = 8, height = 5, dpi = 300)
  ggsave(file.path(OUT_DIR, "Figure_2.png"), make_figure2(dat),
         width = 8, height = 5, dpi = 300)
  ggsave(file.path(OUT_DIR, "Figure_3.png"), make_figure3(med, deltas),
         width = 7, height = 8, dpi = 300)

  ## console summary ---------------------------------------------------------
  cat("\n=== REPLICATION COMPLETE ===\n")
  cat("Rows:", nrow(dat), " Participants:", nlevels(dat$ID), "\n")
  cat("GEE QIC (AR1 vs exchangeable):\n"); print(gee$qic)
  cat("LMM fixed effects (anova):\n");      print(lmm$anova)
  cat("Mediation indirect effect (a*b):\n")
  print(med$paths %>% filter(label == "indirect") %>%
          select(label, est, se, pvalue, lower, upper))
  cat("\nAll CSV tables and figures written to: ", OUT_DIR, "\n")
  invisible(list(data = dat, descriptives = desc, correlations = corr,
                 gee = gee, lmm = lmm, mediation = med, deltas = deltas))
}

## -----------------------------------------------------------------------------
## Entry point: uncomment to run everything non-interactively.
## -----------------------------------------------------------------------------
## results <- run_all()
###############################################################################
