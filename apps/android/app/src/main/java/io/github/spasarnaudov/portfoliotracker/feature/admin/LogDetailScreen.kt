package io.github.spasarnaudov.portfoliotracker.feature.admin

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.ui.components.EmptyState
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenError
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenLoading
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LoadStatus

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LogDetailScreen(
    onNavigateBack: () -> Unit,
    viewModel: LogDetailViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(state.name) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        when (state.status) {
            LoadStatus.LOADING -> FullScreenLoading(modifier = Modifier.padding(padding))
            LoadStatus.ERROR -> FullScreenError(
                message = state.errorMessage ?: "Something went wrong.",
                modifier = Modifier.padding(padding),
                onRetry = viewModel::load,
            )

            LoadStatus.EMPTY -> EmptyState(message = "This log file is empty.", modifier = Modifier.padding(padding))

            LoadStatus.CONTENT -> LazyColumn(modifier = Modifier.fillMaxSize().padding(padding)) {
                items(state.lines) { line ->
                    Text(text = line, fontFamily = FontFamily.Monospace, modifier = Modifier.padding(horizontal = 8.dp))
                }
            }
        }
    }
}
