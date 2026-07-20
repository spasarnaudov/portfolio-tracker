package io.github.spasarnaudov.portfoliotracker.feature.connection

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.ui.components.ConfirmDialog

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConnectionSettingsScreen(
    onNavigateBack: () -> Unit,
    onSessionCleared: () -> Unit,
    viewModel: ConnectionSettingsViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(Unit) {
        viewModel.sessionCleared.collect { onSessionCleared() }
    }
    LaunchedEffect(state.isSaved) {
        if (state.isSaved) snackbarHostState.showSnackbar("Connection settings saved.")
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text("Connection settings") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp)) {
            Text(
                "The server address must be reachable from this device and end with a trailing slash.",
                style = MaterialTheme.typography.bodyMedium,
            )
            Spacer(modifier = Modifier.padding(top = 16.dp))
            OutlinedTextField(
                value = state.baseUrlText,
                onValueChange = viewModel::onUrlChange,
                label = { Text("API base URL") },
                singleLine = true,
                isError = state.validationError != null,
                supportingText = { state.validationError?.let { Text(it) } },
                modifier = Modifier.fillMaxWidth(),
            )
            if (state.isUsingOverride) {
                Spacer(modifier = Modifier.padding(top = 4.dp))
                Text("Using a custom server address.", style = MaterialTheme.typography.labelSmall)
            }

            Spacer(modifier = Modifier.padding(top = 16.dp))
            Row {
                OutlinedButton(onClick = viewModel::testConnection, enabled = !state.isTesting) {
                    if (state.isTesting) {
                        CircularProgressIndicator(modifier = Modifier.padding(2.dp))
                    } else {
                        Text("Test connection")
                    }
                }
                Spacer(modifier = Modifier.padding(start = 8.dp))
                Button(onClick = viewModel::save) { Text("Save") }
            }

            state.testResultMessage?.let {
                Spacer(modifier = Modifier.padding(top = 8.dp))
                Text(
                    text = it,
                    color = if (state.testSucceeded == true) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.error
                    },
                )
            }

            Spacer(modifier = Modifier.padding(top = 24.dp))
            OutlinedButton(onClick = viewModel::resetToDefault, modifier = Modifier.fillMaxWidth()) {
                Text("Reset to default")
            }
        }
    }

    if (state.showClearSessionConfirm) {
        ConfirmDialog(
            title = "Switch server?",
            text = "Changing the server address will sign you out of the current session. Continue?",
            confirmLabel = "Continue",
            destructive = true,
            onConfirm = viewModel::confirmSaveAndClearSession,
            onDismiss = viewModel::dismissClearSessionConfirm,
        )
    }
}
