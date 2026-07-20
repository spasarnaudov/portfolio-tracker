package io.github.spasarnaudov.portfoliotracker.core.model

data class User(
    val id: Long,
    val username: String,
    val role: String,
) {
    val isAdmin: Boolean get() = role.equals("admin", ignoreCase = true)
}
