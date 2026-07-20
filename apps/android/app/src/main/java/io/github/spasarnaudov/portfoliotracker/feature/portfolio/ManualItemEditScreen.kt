package io.github.spasarnaudov.portfoliotracker.feature.portfolio

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ManualItemEditScreen(
    clientKey: String?,
    portfolioViewModel: PortfolioViewModel,
    onDone: () -> Unit,
) {
    val portfolioState by portfolioViewModel.uiState.collectAsState()
    val existing = clientKey?.let { key -> portfolioState.manualItems.firstOrNull { it.clientKey == key } }
    val isNew = existing == null

    var name by remember(clientKey) { mutableStateOf(existing?.name ?: "") }
    var quantityText by remember(clientKey) { mutableStateOf(existing?.quantityText ?: "") }
    var unitPriceText by remember(clientKey) { mutableStateOf(existing?.unitPriceText ?: "") }
    var priceAssetId by remember(clientKey) { mutableStateOf(existing?.priceAssetId) }
    var includeInChart by remember(clientKey) { mutableStateOf(existing?.includeInChart ?: true) }
    var nameError by remember { mutableStateOf<String?>(null) }
    var expanded by remember { mutableStateOf(false) }

    val goldBuybackAssets = portfolioState.goldBuybackAssets
    val selectedAssetLabel = goldBuybackAssets.firstOrNull { it.id == priceAssetId }?.let { "${it.symbol} · ${it.name}" }
        ?: "Manual price"

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (isNew) "Add manual item" else "Edit manual item") },
                navigationIcon = {
                    IconButton(onClick = onDone) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (!isNew) {
                        IconButton(onClick = {
                            clientKey?.let { portfolioViewModel.markManualItemForDeletion(it) }
                            onDone()
                        }) {
                            Icon(Icons.Filled.Delete, contentDescription = "Delete")
                        }
                    }
                },
            )
        },
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp)) {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it; nameError = null },
                label = { Text("Name") },
                singleLine = true,
                isError = nameError != null,
                supportingText = { nameError?.let { Text(it) } },
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(modifier = Modifier.padding(top = 8.dp))
            OutlinedTextField(
                value = quantityText,
                onValueChange = { quantityText = it },
                label = { Text("Quantity") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(modifier = Modifier.padding(top = 8.dp))

            ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
                OutlinedTextField(
                    value = selectedAssetLabel,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Price source") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                    modifier = Modifier.fillMaxWidth().menuAnchor(androidx.compose.material3.ExposedDropdownMenuAnchorType.PrimaryEditable, true),
                )
                DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                    DropdownMenuItem(text = { Text("Manual price") }, onClick = { priceAssetId = null; expanded = false })
                    goldBuybackAssets.forEach { asset ->
                        DropdownMenuItem(
                            text = { Text("${asset.symbol} · ${asset.name}") },
                            onClick = { priceAssetId = asset.id; expanded = false },
                        )
                    }
                }
            }

            if (priceAssetId == null) {
                Spacer(modifier = Modifier.padding(top = 8.dp))
                OutlinedTextField(
                    value = unitPriceText,
                    onValueChange = { unitPriceText = it },
                    label = { Text("Unit price (manual)") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.fillMaxWidth(),
                )
            }

            Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Checkbox(checked = includeInChart, onCheckedChange = { includeInChart = it })
                Text("Include in chart")
            }

            Spacer(modifier = Modifier.padding(top = 16.dp))
            Button(
                onClick = {
                    if (name.isBlank()) {
                        nameError = "Name is required."
                        return@Button
                    }
                    portfolioViewModel.upsertManualItem(
                        (existing ?: ManualItemDraft.blank().copy(clientKey = clientKey ?: java.util.UUID.randomUUID().toString())).copy(
                            name = name.trim(),
                            quantityText = quantityText,
                            unitPriceText = unitPriceText,
                            priceAssetId = priceAssetId,
                            includeInChart = includeInChart,
                        ),
                    )
                    onDone()
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Save")
            }
        }
    }
}
