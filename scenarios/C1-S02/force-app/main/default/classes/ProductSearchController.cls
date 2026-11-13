public with sharing class ProductSearchController {
    private static final Set<String> ALLOWED_SORT_FIELDS = new Set<String>{
        'Name', 'ProductCode', 'CreatedDate', 'LastModifiedDate'
    };

    @AuraEnabled(cacheable=true)
    public static List<Product2> searchProducts(String nameFilter, String sortField) {
        String orderBy = ALLOWED_SORT_FIELDS.contains(sortField) ? sortField : 'Name';
        String query = 'SELECT Id, Name, ProductCode, Description FROM Product2 '
            + 'WHERE IsActive = true AND Name LIKE :nameFilter '
            + 'ORDER BY ' + orderBy + ' ASC LIMIT 100';
        return Database.queryWithBinds(
            query,
            new Map<String, Object>{ 'nameFilter' => '%' + nameFilter + '%' },
            AccessLevel.USER_MODE
        );
    }
}
