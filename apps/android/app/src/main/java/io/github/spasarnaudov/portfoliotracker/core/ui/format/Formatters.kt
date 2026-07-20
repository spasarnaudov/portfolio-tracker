package io.github.spasarnaudov.portfoliotracker.core.ui.format

import java.math.BigDecimal
import java.math.RoundingMode
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale

/** Formats money for display with exactly two decimals; never mutates the source value. */
fun BigDecimal.formatMoney(locale: Locale = Locale.getDefault()): String {
    val scaled = setScale(2, RoundingMode.HALF_UP)
    return String.format(locale, "%,.2f", scaled)
}

fun BigDecimal?.formatMoneyOrDash(locale: Locale = Locale.getDefault()): String =
    this?.formatMoney(locale) ?: "—"

/** Formats a quantity, keeping up to 8 fractional digits without trailing zeros. */
fun BigDecimal.formatQuantity(): String {
    val stripped = stripTrailingZeros().let { if (it.scale() < 0) it.setScale(0) else it }
    val bounded = if (stripped.scale() > 8) stripped.setScale(8, RoundingMode.HALF_UP) else stripped
    return bounded.toPlainString()
}

private val dateFormatter = DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM)
private val dateTimeFormatter = DateTimeFormatter.ofLocalizedDateTime(FormatStyle.MEDIUM, FormatStyle.SHORT)
private val chartAxisDateFormatter = DateTimeFormatter.ofPattern("MMM d")
private val chartAxisDateTimeFormatter = DateTimeFormatter.ofPattern("MMM d, HH:mm")

fun LocalDate.formatDisplay(): String = format(dateFormatter)
fun LocalDateTime.formatDisplay(): String = format(dateTimeFormatter)
fun LocalDateTime.formatChartAxis(showTime: Boolean): String =
    format(if (showTime) chartAxisDateTimeFormatter else chartAxisDateFormatter)
