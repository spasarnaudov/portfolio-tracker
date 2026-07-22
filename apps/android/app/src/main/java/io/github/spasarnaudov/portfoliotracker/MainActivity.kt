package io.github.spasarnaudov.portfoliotracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import dagger.hilt.android.AndroidEntryPoint
import io.github.spasarnaudov.portfoliotracker.navigation.AppNavHost
import io.github.spasarnaudov.portfoliotracker.ui.theme.PortfolioTrackerAndroidTheme

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PortfolioTrackerAndroidTheme {
                AppNavHost()
            }
        }
    }
}
