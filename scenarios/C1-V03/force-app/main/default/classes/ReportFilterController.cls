public with sharing class ReportFilterController {
    @AuraEnabled(cacheable=true)
    public static List<Opportunity> getFilteredOpportunities(List<String> fieldFilters) {
        // fieldFilters is a list of "fieldName=value" strings from the client
        String whereClause = '';
        for (String filter : fieldFilters) {
            if (String.isNotBlank(whereClause)) {
                whereClause += ' AND ';
            }
            // VULNERABLE: field name and value are concatenated verbatim with no allow-list or escaping
            whereClause += filter;
        }
        String query = 'SELECT Id, Name, Amount, StageName FROM Opportunity';
        if (String.isNotBlank(whereClause)) {
            query += ' WHERE ' + whereClause;
        }
        return Database.query(query, AccessLevel.USER_MODE);
    }
}
