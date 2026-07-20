package io.github.spasarnaudov.portfoliotracker.feature.account

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenError
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenLoading
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LoadStatus

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountScreen(
    onLoggedOut: () -> Unit,
    onChangePassword: () -> Unit,
    onDeleteAccount: () -> Unit,
    onConnectionSettings: () -> Unit,
    viewModel: AccountViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loggedOut.collect { onLoggedOut() }
    }

    Scaffold(topBar = { TopAppBar(title = { Text("Account") }) }) { padding ->
        when (state.status) {
            LoadStatus.LOADING -> FullScreenLoading(modifier = Modifier.padding(padding))
            LoadStatus.ERROR -> FullScreenError(
                message = state.errorMessage ?: "Something went wrong.",
                modifier = Modifier.padding(padding),
                onRetry = viewModel::load,
            )

            else -> Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp)) {
                state.user?.let { user ->
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(user.username, style = MaterialTheme.typography.titleLarge)
                            Text("Role: ${user.role}", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }

                Spacer(modifier = Modifier.padding(top = 16.dp))
                OutlinedButton(onClick = onChangePassword, modifier = Modifier.fillMaxWidth()) {
                    Text("Change password")
                }
                Spacer(modifier = Modifier.padding(top = 8.dp))
                OutlinedButton(onClick = onConnectionSettings, modifier = Modifier.fillMaxWidth()) {
                    Text("Connection settings")
                }

                Spacer(modifier = Modifier.padding(top = 24.dp))
                Button(
                    onClick = viewModel::logout,
                    enabled = !state.isLoggingOut,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(if (state.isLoggingOut) "Signing out…" else "Log out")
                }
                Spacer(modifier = Modifier.padding(top = 8.dp))
                Button(
                    onClick = onDeleteAccount,
                    colors = androidx.compose.material3.ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Delete account")
                }
            }
        }
    }
}
