package io.github.spasarnaudov.portfoliotracker.feature.account

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.ui.components.ConfirmDialog

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeleteAccountScreen(
    onAccountDeleted: () -> Unit,
    onNavigateBack: () -> Unit,
    viewModel: DeleteAccountViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()
    var showConfirm by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.accountDeleted.collect { onAccountDeleted() }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Delete account") },
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
                "Deleting your account is permanent. You will be signed out and will no longer be able to access your portfolio.",
                style = MaterialTheme.typography.bodyLarge,
            )
            state.errorMessage?.let {
                Spacer(modifier = Modifier.padding(top = 16.dp))
                Text(it, color = MaterialTheme.colorScheme.error)
            }
            Spacer(modifier = Modifier.padding(top = 24.dp))
            Button(
                onClick = { showConfirm = true },
                enabled = !state.isSubmitting,
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (state.isSubmitting) "Deleting…" else "Delete my account")
            }
        }
    }

    if (showConfirm) {
        ConfirmDialog(
            title = "Delete account?",
            text = "This cannot be undone. Are you sure you want to permanently delete your account?",
            confirmLabel = "Delete",
            destructive = true,
            onConfirm = { showConfirm = false; viewModel.confirmDeletion() },
            onDismiss = { showConfirm = false },
        )
    }
}
