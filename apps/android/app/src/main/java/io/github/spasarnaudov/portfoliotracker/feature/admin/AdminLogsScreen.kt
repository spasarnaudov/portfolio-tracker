package io.github.spasarnaudov.portfoliotracker.feature.admin

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.ListItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.model.LogFile
import io.github.spasarnaudov.portfoliotracker.core.ui.components.EmptyState
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenError
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenLoading
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LoadStatus
import io.github.spasarnaudov.portfoliotracker.core.ui.format.formatDisplay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminLogsScreen(
    onLogClick: (LogFile) -> Unit,
    viewModel: AdminLogsViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("Log files") }) }) { padding ->
        when (state.status) {
            LoadStatus.LOADING -> FullScreenLoading(modifier = Modifier.padding(padding))
            LoadStatus.ERROR -> FullScreenError(
                message = state.errorMessage ?: "Something went wrong.",
                modifier = Modifier.padding(padding),
                onRetry = viewModel::load,
            )

            LoadStatus.EMPTY -> EmptyState(message = "No log files found.", modifier = Modifier.padding(padding))

            LoadStatus.CONTENT -> LazyColumn(modifier = Modifier.fillMaxSize().padding(padding)) {
                items(state.files, key = { it.name }) { file ->
                    ListItem(
                        headlineContent = { Text(file.name) },
                        supportingContent = {
                            val size = file.sizeBytes?.let { "${it / 1024} KB" }
                            val modified = file.modifiedAt?.formatDisplay()
                            Text(listOfNotNull(size, modified).joinToString(" · "))
                        },
                        modifier = Modifier.fillMaxWidth().clickable { onLogClick(file) },
                    )
                    HorizontalDivider()
                }
            }
        }
    }
}
