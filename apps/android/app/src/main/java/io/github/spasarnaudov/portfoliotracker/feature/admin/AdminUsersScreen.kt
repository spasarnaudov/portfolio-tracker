package io.github.spasarnaudov.portfoliotracker.feature.admin

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.ListItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.PrimaryTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.model.AdminUserSummary
import io.github.spasarnaudov.portfoliotracker.core.model.LoginHistoryEntry
import io.github.spasarnaudov.portfoliotracker.core.model.LoginStatEntry
import io.github.spasarnaudov.portfoliotracker.core.ui.components.EmptyState
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenError
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenLoading
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LoadStatus

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminUsersScreen(viewModel: AdminUsersViewModel = hiltViewModel()) {
    val state by viewModel.uiState.collectAsState()
    val tabs = AdminTab.entries

    Scaffold(topBar = { TopAppBar(title = { Text("Admin") }) }) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            PrimaryTabRow(selectedTabIndex = tabs.indexOf(state.selectedTab)) {
                tabs.forEach { tab ->
                    Tab(
                        selected = state.selectedTab == tab,
                        onClick = { viewModel.selectTab(tab) },
                        text = { Text(tab.label()) },
                    )
                }
            }

            when (state.selectedTab) {
                AdminTab.USERS -> UsersTab(state.usersStatus, state.users, state.usersError, viewModel::loadUsers)
                AdminTab.LOGIN_STATS -> LoginStatsTab(state.loginStatsStatus, state.loginStats, state.loginStatsError, viewModel::loadLoginStats)
                AdminTab.LOGIN_HISTORY -> LoginHistoryTab(state.loginHistoryStatus, state.loginHistory, state.loginHistoryError, viewModel::loadLoginHistory)
            }
        }
    }
}

private fun AdminTab.label(): String = when (this) {
    AdminTab.USERS -> "Users"
    AdminTab.LOGIN_STATS -> "Login stats"
    AdminTab.LOGIN_HISTORY -> "Login history"
}

@Composable
private fun UsersTab(status: LoadStatus, users: List<AdminUserSummary>, error: String?, onRetry: () -> Unit) {
    when (status) {
        LoadStatus.LOADING -> FullScreenLoading()
        LoadStatus.ERROR -> FullScreenError(message = error ?: "Something went wrong.", onRetry = onRetry)
        LoadStatus.EMPTY -> EmptyState(message = "No users found.")
        LoadStatus.CONTENT -> LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(users, key = { it.id }) { user ->
                ListItem(
                    headlineContent = { Text(user.username) },
                    supportingContent = { Text("Role: ${user.role}${user.active?.let { active -> if (!active) " · inactive" else "" } ?: ""}") },
                    modifier = Modifier.fillMaxWidth(),
                )
                HorizontalDivider()
            }
        }
    }
}

@Composable
private fun LoginStatsTab(status: LoadStatus, stats: List<LoginStatEntry>, error: String?, onRetry: () -> Unit) {
    when (status) {
        LoadStatus.LOADING -> FullScreenLoading()
        LoadStatus.ERROR -> FullScreenError(message = error ?: "Something went wrong.", onRetry = onRetry)
        LoadStatus.EMPTY -> EmptyState(message = "No login statistics available.")
        LoadStatus.CONTENT -> LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(stats) { entry ->
                ListItem(headlineContent = { Text(entry.label) }, supportingContent = { Text(entry.value) })
                HorizontalDivider()
            }
        }
    }
}

@Composable
private fun LoginHistoryTab(status: LoadStatus, history: List<LoginHistoryEntry>, error: String?, onRetry: () -> Unit) {
    when (status) {
        LoadStatus.LOADING -> FullScreenLoading()
        LoadStatus.ERROR -> FullScreenError(message = error ?: "Something went wrong.", onRetry = onRetry)
        LoadStatus.EMPTY -> EmptyState(message = "No login history available.")
        LoadStatus.CONTENT -> LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(history) { entry ->
                ListItem(
                    headlineContent = { Text(entry.fields.joinToString(" · ") { "${it.label}: ${it.value}" }) },
                )
                HorizontalDivider()
            }
        }
    }
}
