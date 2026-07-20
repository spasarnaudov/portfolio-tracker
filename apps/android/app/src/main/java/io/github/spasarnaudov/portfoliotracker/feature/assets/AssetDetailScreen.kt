package io.github.spasarnaudov.portfoliotracker.feature.assets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.model.AssetPriceInterval
import io.github.spasarnaudov.portfoliotracker.core.model.ChartRange
import io.github.spasarnaudov.portfoliotracker.core.ui.components.ChartPoint
import io.github.spasarnaudov.portfoliotracker.core.ui.components.EmptyState
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenError
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenLoading
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LineChart
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LoadStatus
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AssetDetailScreen(
    onNavigateBack: () -> Unit,
    viewModel: AssetDetailViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()
    var showStartPicker by remember { mutableStateOf(false) }
    var showEndPicker by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("${state.symbol} · ${state.name}") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp)) {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(ChartRange.entries) { range ->
                    FilterChip(
                        selected = state.range == range,
                        onClick = { viewModel.setRange(range) },
                        label = { Text(range.label) },
                    )
                }
            }
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                items(AssetPriceInterval.entries) { interval ->
                    FilterChip(
                        selected = state.interval == interval,
                        onClick = { viewModel.setInterval(interval) },
                        label = { Text(interval.label) },
                    )
                }
            }

            if (state.range == ChartRange.CUSTOM) {
                Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = { showStartPicker = true }) {
                        Text(state.customStartDate?.toString() ?: "Start date")
                    }
                    TextButton(onClick = { showEndPicker = true }) {
                        Text(state.customEndDate?.toString() ?: "End date")
                    }
                    Button(
                        onClick = viewModel::applyCustomRange,
                        enabled = state.customStartDate != null && state.customEndDate != null,
                    ) {
                        Text("Apply")
                    }
                }
            }

            when (state.status) {
                LoadStatus.LOADING -> FullScreenLoading()
                LoadStatus.ERROR -> FullScreenError(
                    message = state.errorMessage ?: "Something went wrong.",
                    onRetry = viewModel::load,
                )

                LoadStatus.EMPTY -> EmptyState(message = "No price history for this range yet.")
                LoadStatus.CONTENT -> LineChart(
                    points = state.points.map { ChartPoint(it.timestamp, it.price) },
                    showTimeInLabels = state.interval == AssetPriceInterval.HOURLY || state.interval == AssetPriceInterval.RECORDED,
                    modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
                )
            }
        }
    }

    if (showStartPicker) {
        val datePickerState = rememberDatePickerState()
        DatePickerDialog(
            onDismissRequest = { showStartPicker = false },
            confirmButton = {
                TextButton(onClick = {
                    datePickerState.selectedDateMillis?.let {
                        viewModel.setCustomDates(millisToLocalDate(it), state.customEndDate)
                    }
                    showStartPicker = false
                }) { Text("OK") }
            },
            dismissButton = { TextButton(onClick = { showStartPicker = false }) { Text("Cancel") } },
        ) {
            DatePicker(state = datePickerState)
        }
    }

    if (showEndPicker) {
        val datePickerState = rememberDatePickerState()
        DatePickerDialog(
            onDismissRequest = { showEndPicker = false },
            confirmButton = {
                TextButton(onClick = {
                    datePickerState.selectedDateMillis?.let {
                        viewModel.setCustomDates(state.customStartDate, millisToLocalDate(it))
                    }
                    showEndPicker = false
                }) { Text("OK") }
            },
            dismissButton = { TextButton(onClick = { showEndPicker = false }) { Text("Cancel") } },
        ) {
            DatePicker(state = datePickerState)
        }
    }
}

private fun millisToLocalDate(millis: Long): LocalDate =
    Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate()
